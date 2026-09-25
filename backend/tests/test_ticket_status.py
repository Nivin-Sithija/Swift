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
