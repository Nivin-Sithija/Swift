"""Status transitions for assignment and escalation, and what their responses report.

set_status guards every jump with can_transition; the assignment and escalation routes
change the status too, so they are held to the same rules here. Both also change a
related row (agent, queue), which the response body has to reflect.
"""

from app.models.entities import SupportQueue


async def close_ticket(client, ticket: str, headers) -> None:
    await client.put(f"/tickets/{ticket}/assignment", json={}, headers=headers)
    for status in ("response_draft", "responded", "resolved", "closed"):
        response = await client.put(
            f"/tickets/{ticket}/status", json={"status": status}, headers=headers
        )
        assert response.status_code == 200, response.text


async def test_a_closed_ticket_cannot_be_reassigned(client, customer, agent, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    staff = auth_headers(agent)
    await close_ticket(client, ticket, staff)

    response = await client.put(f"/tickets/{ticket}/assignment", json={}, headers=staff)

    assert response.status_code == 409, "a closed ticket was assigned, reviving it"
    assert (await client.get(f"/tickets/{ticket}", headers=staff)).json()["status"] == "closed"


async def test_a_closed_ticket_cannot_be_escalated(client, customer, agent, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    staff = auth_headers(agent)
    await close_ticket(client, ticket, staff)

    response = await client.post(
        f"/tickets/{ticket}/escalate", json={"reason": "Customer called again"}, headers=staff
    )

    assert response.status_code == 409
    assert (await client.get(f"/tickets/{ticket}", headers=staff)).json()["status"] == "closed"


async def test_an_open_ticket_can_still_be_escalated(client, customer, agent, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    staff = auth_headers(agent)

    response = await client.post(
        f"/tickets/{ticket}/escalate", json={"reason": "Possible fraud on the account"}, headers=staff
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "escalated"


async def test_assignment_response_names_the_assigned_agent(
    client, customer, agent, new_ticket, auth_headers
):
    ticket = await new_ticket(customer)

    body = (await client.put(f"/tickets/{ticket}/assignment", json={}, headers=auth_headers(agent))).json()

    # Staff act on this response directly, so a stale null would show as unassigned.
    assert body["assigned_agent"] == agent.full_name
    assert body["status"] == "assigned"


async def test_escalation_response_names_the_new_queue(
    client, customer, agent, new_ticket, auth_headers, db
):
    db.add(SupportQueue(name="Fraud & Security"))
    await db.commit()
    ticket = await new_ticket(customer)

    body = (
        await client.post(
            f"/tickets/{ticket}/escalate",
            json={"reason": "Possible fraud on the account"},
            headers=auth_headers(agent),
        )
    ).json()

    assert body["assigned_queue"] == "Fraud & Security"
    assert body["escalation_reason"] == "Possible fraud on the account"

async def test_agent_picker_lists_staff_only(client, customer, agent, auth_headers):
    response = await client.get("/agents", headers=auth_headers(agent))
    assert response.status_code == 200
    assert {"id": str(agent.id), "name": agent.full_name} in response.json()
    assert all(item["id"] != str(customer.id) for item in response.json())
    assert (await client.get("/agents", headers=auth_headers(customer))).status_code == 403


async def test_response_approval_and_send_record_activity(client, customer, agent, new_ticket, auth_headers):
    ticket_id = await new_ticket(customer)
    headers = auth_headers(agent)
    ticket = (await client.get(f"/tickets/{ticket_id}", headers=headers)).json()
    response_id = ticket["responses"][0]["id"]
    approved = await client.post(f"/responses/{response_id}/approve", headers=headers)
    assert approved.status_code == 200, approved.text
    sent = await client.post(f"/responses/{response_id}/send", headers=headers)
    assert sent.status_code == 200, sent.text
    updated = (await client.get(f"/tickets/{ticket_id}", headers=headers)).json()
    assert updated["status"] == "responded"
    assert any(event["label"] == "Response Sent" for event in updated["events"])


async def test_undo_escalation_returns_to_support_and_preserves_agent(
    client, customer, agent, new_ticket, auth_headers, db
):
    db.add_all([SupportQueue(name="General Support"), SupportQueue(name="Fraud & Security")])
    await db.commit()
    ticket = await new_ticket(customer)
    headers = auth_headers(agent)
    await client.put(f"/tickets/{ticket}/assignment", json={}, headers=headers)
    await client.post(f"/tickets/{ticket}/escalate", json={"reason": "Specialist review needed"}, headers=headers)
    response = await client.post(f"/tickets/{ticket}/undo-escalation", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "assigned"
    assert body["assigned_agent"] == agent.full_name
    assert body["assigned_queue"] == "General Support"
    assert body["escalation_reason"] is None
    assert any(e["label"] == "Escalated" for e in body["events"])
    assert any(e["label"] == "Escalation Undone" for e in body["events"])
    assert (await client.get(f"/tickets/{ticket}", headers=headers)).json()["status"] == "assigned"
    assert (await client.post(f"/tickets/{ticket}/undo-escalation", headers=headers)).status_code == 409


async def test_undo_unassigned_escalation_returns_to_review(client, customer, agent, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    headers = auth_headers(agent)
    await client.post(f"/tickets/{ticket}/escalate", json={"reason": "Specialist review needed"}, headers=headers)
    response = await client.post(f"/tickets/{ticket}/undo-escalation", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "in_review"
    assert response.json()["assigned_agent"] is None


async def test_undo_resolution_reopens_and_retains_history(client, customer, agent, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    headers = auth_headers(agent)
    await client.put(f"/tickets/{ticket}/assignment", json={}, headers=headers)
    await client.put(f"/tickets/{ticket}/status", json={"status": "resolved"}, headers=headers)
    response = await client.post(f"/tickets/{ticket}/undo-resolution", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "reopened"
    assert body["assigned_agent"] == agent.full_name
    assert any(e["label"] == "Resolution Undone" for e in body["events"])
    assert (await client.get(f"/tickets/{ticket}", headers=headers)).json()["status"] == "reopened"
    assert (await client.post(f"/tickets/{ticket}/undo-resolution", headers=headers)).status_code == 409


async def test_undo_is_staff_only_and_does_not_reopen_closed_tickets(client, customer, agent, new_ticket, auth_headers):
    ticket = await new_ticket(customer)
    await close_ticket(client, ticket, auth_headers(agent))
    for action in ("undo-resolution", "undo-escalation"):
        assert (await client.post(f"/tickets/{ticket}/{action}", headers=auth_headers(customer))).status_code == 403
        assert (await client.post(f"/tickets/{ticket}/{action}", headers=auth_headers(agent))).status_code == 409
