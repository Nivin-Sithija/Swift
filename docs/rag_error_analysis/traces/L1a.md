# `L1a` — language detection

Tamilish accuracy 25.6% [24.1%, 27.2%] over n=3079. Each ticket below is detected correctly in the other four languages and wrongly only in tamilish, so the failure is the detector, not the ticket.

```
id 0
  en  : How do I locate my card?
  ta* : Enoda card-ai naan eppadi kandupidikkuthu?
  -> detected as: english
```

```
id 1
  en  : I still have not received my new card, I ordered over a week ago.
  ta* : Naan oru vaaraththukku munbe order seithum, enoda puthiya card innum enakku kidaikkala.
  -> detected as: english
```

```
id 2
  en  : I ordered a card but it has not arrived. Help please!
  ta* : Naan oru card-ku order seithen, aanal athu innum varala. please uthavungal!
  -> detected as: english
```

```
id 3
  en  : Is there a way to know when my card will arrive?
  ta* : Enoda card eppo vanthu serum endru therinthukolla ethavathu vazhi irukka?
  -> detected as: english
```

```
id 4
  en  : My card has not arrived yet.
  ta* : Enoda card innum vanthu serala.
  -> detected as: english
```

```
id 5
  en  : When will I get my card?
  ta* : Enoda card enakku eppo kidaikkum?
  -> detected as: english
```
