"""Synthetic data only. No real card data. Run: python db/seed.py"""
import os, random, datetime as dt, psycopg
random.seed(7)
DSN = os.getenv("ADMIN_DSN", "postgresql://postgres:postgres@localhost:5432/disputes")
NOW = dt.datetime(2026, 9, 1, 12, tzinfo=dt.timezone.utc)
MERCH = [("M1","Acme Electronics","retail","US",0.01),("M2","QuickShip Online","ecom","US",0.09),
         ("M3","Berlin Bistro","dining","DE",0.005),("M4","EuroTravel","travel","FR",0.02)]
KINDS = ["fraud_foreign","fraud_friendly","dup_real","dup_false","inr_real","inr_false","other"]
REASON = {"fraud_foreign":"fraud","fraud_friendly":"fraud","dup_real":"duplicate","dup_false":"duplicate",
          "inr_real":"not_received","inr_false":"not_received","other":"quality"}
with psycopg.connect(DSN, autocommit=True) as c:
    for m in MERCH: c.execute("INSERT INTO merchants VALUES (%s,%s,%s,%s,%s)", m)
    for i in range(28):
        kind = KINDS[i % len(KINDS)]; home = random.choice(["US","EU"]); tok = f"tok_{i:04d}"
        l4 = f"{random.randint(0,9999):04d}"; mid = "M3" if home=="EU" else "M1"
        n = [0]
        def add(merch, amt, mins_ago, region, channel="online", delivered=True):
            n[0]+=1; tid=f"t{i:03d}_{n[0]}"
            c.execute("INSERT INTO transactions VALUES (%s,%s,%s,%s,%s,'USD',%s,%s,%s,%s)",
              (tid,tok,l4,merch,amt,NOW-dt.timedelta(minutes=mins_ago),region,channel,delivered)); return tid
        for d in range(3): add(mid, random.randint(10,90), 60*24*(d+3), home, "pos")
        amt = random.choice([45, 240, 1450])
        if kind=="fraud_foreign": t = add("M2", amt, 120, "EU" if home=="US" else "US")
        elif kind=="fraud_friendly": t = add(mid, amt, 120, home)
        elif kind=="dup_real": add(mid, amt, 130, home); t = add(mid, amt, 120, home)
        elif kind=="dup_false": t = add(mid, amt, 120, home)
        elif kind=="inr_real": t = add("M2", amt, 60*24*10, home, delivered=False)
        elif kind=="inr_false": t = add("M2", amt, 60*24*10, home, delivered=True)
        else: t = add("M4", amt, 120, home)
        c.execute("INSERT INTO disputes VALUES (%s,%s,%s,%s,%s)",
          (f"D{i:03d}", t, REASON[kind], f"Cardholder claims {REASON[kind]} issue", home))
print("seeded")
