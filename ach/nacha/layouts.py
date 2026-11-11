"""NACHA record layouts: 0-based (start, end) slices into each 94-character line."""

RECORD_LENGTH = 94
BLOCKING_FACTOR = 10
PADDING_LINE = "9" * RECORD_LENGTH
HASH_MODULUS = 10**10

ACH_FIELDS = {
    "1": {
        "record_type": (0, 1),
        "priority_code": (1, 3),
        "immediate_dest": (3, 13),
        "immediate_origin": (13, 23),
        "create_date": (23, 29),
        "create_time": (29, 33),
        "id_modifier": (33, 34),
        "record_size": (34, 37),
        "blocking_factor": (37, 39),
        "format_code": (39, 40),
        "destination_bank": (40, 63),
        "origin_company": (63, 86),
        "reference_code": (86, 94),
    },
    "5": {
        "record_type": (0, 1),
        "service_class": (1, 4),  # 220 credits, 225 debits, 200 mixed
        "company_name": (4, 20),
        "discretionary": (20, 40),
        "company_id": (40, 50),
        "sec_code": (50, 53),  # PPD, CCD, ...
        "entry_description": (53, 63),
        "descriptive_date": (63, 69),
        "effective_date": (69, 75),  # YYMMDD: when the money moves
        "settlement_date": (75, 78),  # blank: filled in by the ACH operator
        "originator_status": (78, 79),
        "originating_dfi": (79, 87),
        "batch_number": (87, 94),
    },
    "6": {
        "record_type": (0, 1),
        "transaction_code": (1, 3),
        "routing_number": (3, 11),
        "check_digit": (11, 12),
        "account_number": (12, 29),
        "amount": (29, 39),
        "individual_id": (39, 54),
        "individual_name": (54, 76),
        "discretionary": (76, 78),
        "addenda_flag": (78, 79),
        "trace_number": (79, 94),
    },
    "7": {
        "record_type": (0, 1),
        "addenda_type": (1, 3),
        "payment_info": (3, 83),
        "addenda_seq": (83, 87),
        "entry_seq": (87, 94),  # last 7 digits of its entry's trace number
    },
    "8": {
        "record_type": (0, 1),
        "service_class": (1, 4),
        "entry_count": (4, 10),  # entries + addenda
        "entry_hash": (10, 20),
        "total_debits": (20, 32),
        "total_credits": (32, 44),
        "company_id": (44, 54),
        "auth_code": (54, 73),  # message authentication code, usually blank
        "reserved": (73, 79),
        "originating_dfi": (79, 87),
        "batch_number": (87, 94),
    },
    "9": {
        "record_type": (0, 1),
        "batch_count": (1, 7),
        "block_count": (7, 13),
        "entry_count": (13, 21),  # entries + addenda, whole file
        "entry_hash": (21, 31),
        "total_debits": (31, 43),
        "total_credits": (43, 55),
        "reserved": (55, 94),
    },
}
