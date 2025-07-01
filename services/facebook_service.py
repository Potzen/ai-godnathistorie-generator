import requests
import os


def post_photo_to_facebook_page(page_id, page_access_token, image_path, caption=""):
    """
    Uploader et lokalt billede med en billedtekst til en Facebook-side.

    Args:
        page_id (str): ID'et for din Facebook-side.
        page_access_token (str): Dit permanente Page Access Token.
        image_path (str): Stien til billedfilen, der skal uploades.
        caption (str, optional): Teksten, der skal ledsage billedet.

    Returns:
        dict: Svaret fra Facebook API'en som en dictionary.

    Raises:
        Exception: Hvis API-kaldet fejler eller billedfilen ikke findes.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Billedfilen blev ikke fundet ved stien: {image_path}")

    # Facebook Graph API endpoint til at poste billeder
    # Bruger v18.0 som et eksempel; du kan opdatere dette efter behov.
    url = f"https://graph.facebook.com/v18.0/{page_id}/photos"

    payload = {
        'caption': caption,
        'access_token': page_access_token
    }

    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'source': image_file
            }

            print(f"Sender anmodning til Facebook for side {page_id}...")
            response = requests.post(url, data=payload, files=files)

            # Kaster en fejl for HTTP-fejlkoder (f.eks. 400, 401, 500)
            response.raise_for_status()

        result = response.json()
        if 'id' in result:
            print(f"Post oprettet succesfuldt på Facebook! Post ID: {result['id']}")
            return result
        else:
            # Dette sker sjældent, hvis raise_for_status() ikke fejler, men for en sikkerheds skyld.
            raise Exception(f"Ukendt svar modtaget fra Facebook: {result}")

    except requests.exceptions.RequestException as e:
        # Giver en mere detaljeret fejlmeddelelse
        error_message = f"Fejl under kommunikation med Facebook API: {e}"
        if e.response is not None:
            error_message += f"\nServer svar: {e.response.text}"
        print(error_message)
        raise Exception(error_message)