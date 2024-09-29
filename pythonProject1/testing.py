from urllib.parse import urlencode

params = {
            "taxonomy_description": "Oncology",
            "city": "Ithaca",
            "first_name": "Jacob",
            "version": "2.1"
        }
print(urlencode(params))