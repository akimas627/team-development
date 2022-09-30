import re
def check_email(email: str):
    pattern = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(pattern, email):
        return True
    else:
        return False

# categoriesをjsonの形に変換する関数
def categories_change_json(categories):
    json = []
    for categorie in categories:
        categorie_dict = {}
        categorie_dict["id"] = categorie.id
        categorie_dict["categorie"] = categorie.categorie
        json.append(categorie_dict)
    return json