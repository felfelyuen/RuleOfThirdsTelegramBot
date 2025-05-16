from firebase_config import db

def get_user_role(telegram_id: int) -> str:
    sellers_ref = db.collection("sellers")
    # Query for documents where the telegram-id field matches
    matching_sellers = sellers_ref.where("telegram_id", "==", telegram_id).stream()
    for _ in matching_sellers:
        return "seller"
    
    return "buyer"


