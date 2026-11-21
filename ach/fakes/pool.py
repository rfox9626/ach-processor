from django.conf import settings
from faker import Faker

def build_pool(seed: int = 42):
    fake = Faker("en_US")
    fake.seed_instance(seed)
    originators = build_originators(fake, 6)
    receivers = build_receivers(fake, 100)
    relationships = build_relationships(originators, receivers, fake)
    return originators, receivers, relationships


def build_originators(fake, n) -> list[dict]: 
    res = []
    for i in range(n):
        # generate 50% billpay / 50% payroll
        if i % 2 != 0:
            kind = "billpay"
        else:
            kind = "payroll"
    
        orig = {
            "id": f"ORIG{i:03d}",
            "company_id": "1" + fake.numerify("#########"),
            "company_name": fake.company(),
            "kind": kind,
        }

        res.append(orig)
    return res


def build_relationships(originators, receivers, fake) -> list[dict]: 
    payroll = [o for o in originators if o["kind"] == "payroll"]
    billpay = [o for o in originators if o["kind"] == "billpay"]
    checking = [r for r in receivers if r["kind"] == "checking"]
    savings = [r for r in receivers if r["kind"] == "savings"]
    relationships = []

    for rec in checking:
        use_pay = fake.random_element(payroll)
        use_bill = fake.random_element(billpay)

        # payroll
        rel = {
            "originator": use_pay["id"], 
            "receiver": rec["id"],
            "individual_id": "EMP" + fake.numerify("########"),
        }

        relationships.append(rel)

        # billpay
        rel = {
            "originator": use_bill["id"], 
            "receiver": rec["id"],
            "individual_id": "CUST" + fake.numerify("########"),
        }

        relationships.append(rel)

    for rec in savings:
        use_pay = fake.random_element(payroll)

        # payroll
        rel = {
            "originator": use_pay["id"], 
            "receiver": rec["id"],
            "individual_id": "EMP" + fake.numerify("########"),
        }

        relationships.append(rel)

    return relationships


def build_receivers(fake, n) -> list[dict]:
    res = []
    for i in range(n):
        # generate 50% savings/50% checking
        if i % 2 != 0:
            kind = "savings"
        else:
            kind = "checking"

        if i % 20 != 0:
            status = "open"
        else:
            status = "closed"

        orig = {
            "id": f"R{i:03d}",
            "name": fake.name(),
            "routing": settings.ACH_BANK_ROUTING,
            "account_number": fake.numerify("#" * fake.random_int(8, 12)),
            "kind": kind,
            "status": status,
        }
    
        res.append(orig)
    return res

