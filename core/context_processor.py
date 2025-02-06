import os


def google_analytics_processor(request):
    env = os.getenv("ENVIRONMENT").lower()

    if env == "prod":
        ga_id = os.getenv("GA_PROD_ID")
    elif env == "stage":
        ga_id = os.getenv("GA_STAGE_ID")
    else:
        ga_id = ""

    usertype = "anonymous"
    if request.user.is_staff and request.user.is_authenticated:
        usertype = "admin"
    elif request.user.is_authenticated:
        usertype = "regular"

    context = {
        "GOOGLE_ANALYTICS_ID": ga_id,
        "USER_TYPE": usertype.lower(),
    }

    return context