import re
from main.models import Libro
from bs4 import BeautifulSoup
import urllib.request
import os, ssl
from main.whoosh_index import update_index
import urllib.parse
import time

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = "http://books.toscrape.com/catalogue/"
BASE_SEARCH = "https://www.goodreads.com/search?q={query}&page={page}"

def scrape_books_to_scrape():
    for page in range(1, 5):
        url = f"{BASE_URL}page-{page}.html"
        try:
            response = urllib.request.urlopen(url)
            soup = BeautifulSoup(response.read(), "lxml")
            books = soup.find_all("article", class_="product_pod")

            for book in books:
                try:
                    titulo = book.h3.a["title"]
                    precio = book.find("p", class_="price_color").get_text(strip=True)
                    disponibilidad = book.find("p", class_="instock availability").get_text(strip=True)
                    rating_class = book.p["class"]
                    rating = rating_class[1] if len(rating_class) > 1 else "None"

                    detalle_url = BASE_URL + book.h3.a["href"]
                    detalle_response = urllib.request.urlopen(detalle_url)
                    detalle_soup = BeautifulSoup(detalle_response.read(), "lxml")

                    categoria = detalle_soup.find("ul", class_="breadcrumb").find_all("li")[2].a.get_text(strip=True)
                    descripcion_tag = detalle_soup.find("div", id="product_description")
                    descripcion = descripcion_tag.find_next_sibling("p").get_text(strip=True) if descripcion_tag else "No disponible"

                    imagen_rel = detalle_soup.find("div", class_="item active").img["src"]
                    imagen_url = "http://books.toscrape.com/" + imagen_rel.replace("../..", "")

                    Libro.objects.create(
                        titulo=titulo,
                        precio=precio,
                        disponibilidad=disponibilidad,
                        categoria=categoria,
                        rating=rating,
                        descripcion=descripcion,
                        imagen_url=imagen_url
                    )
                except Exception as e:
                    print(f"No se pudo crear el libro: {e}")

        except Exception as e:
            print(f"No se pudo abrir la página {url}: {e}")
    update_index()

    print("Base de datos cargada correctamente.")
    return True

NUM_TO_WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}

def scrape_goodreads(query="programming", max_pages=3, delay=1):
    query_encoded = urllib.parse.quote_plus(query)
    
    for page in range(1, max_pages + 1):
        url = BASE_SEARCH.format(query=query_encoded, page=page)
        
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            response = urllib.request.urlopen(request)
            soup = BeautifulSoup(response.read(), "lxml")
            
            items = soup.find_all("tr", itemtype="http://schema.org/Book")
            
            for item in items:
                try:
                    titulo_tag = item.find("a", class_="bookTitle")
                    titulo = titulo_tag.get_text(strip=True) if titulo_tag else "No disponible"

                    rating_tag = item.find("span", class_="minirating")
                    rating_text = rating_tag.get_text(strip=True) if rating_tag else "0"
                    match = re.search(r"(\d+\.?\d*)", rating_text)
                    rating_num = int(float(match.group(1))) if match else 0
                    rating = NUM_TO_WORD.get(rating_num, "none")

                    detalle_url = "https://www.goodreads.com" + titulo_tag["href"] if titulo_tag else ""

                    img_tag = item.find("img")
                    if img_tag:
                        imagen_url = img_tag.get("data-original") or img_tag.get("src") or ""
                        imagen_url = re.sub(r'_[SX|SY]\d+_', '', imagen_url)
                    else:
                        imagen_url = ""

                    try:
                        if detalle_url:
                            det_req = urllib.request.Request(
                                detalle_url,
                                headers={"User-Agent": "Mozilla/5.0"}
                            )
                            det_resp = urllib.request.urlopen(det_req)
                            det_soup = BeautifulSoup(det_resp.read(), "lxml")

                            desc_tag = det_soup.select_one(
                                'div[data-testid="description"] span.Formatted'
                            )
                            descripcion = desc_tag.get_text(strip=True) if desc_tag else "No disponible"
                        else:
                            descripcion = "No disponible"
                    except:
                        descripcion = "No disponible"

                    Libro.objects.create(
                        titulo=titulo,
                        precio="N/A",
                        disponibilidad="N/A",
                        categoria=query.capitalize(),  
                        rating=rating,
                        descripcion=descripcion,
                        imagen_url=imagen_url
                    )

                except Exception as e:
                    print(f"Error detalle Goodreads: {e}")
            
            time.sleep(delay)

        except Exception as e:
            print(f"No se pudo abrir la página de búsqueda Goodreads (page {page}): {e}")
            break

def populateDB():
    Libro.objects.all().delete()

    scrape_books_to_scrape()   
    scrape_goodreads("fantasy", max_pages=1)
    scrape_goodreads("science fiction", max_pages=1)
    scrape_goodreads("romance", max_pages=1)

    update_index()
    print("¡Base de datos completada desde BooksToScrape + Goodreads!")
