
novinky_cz
├── README.txt
├── app.py #vezme sitemap_articles_0.xml a rekurzivne stahne komentare
├── db_models.py
├── done_links.txt #VYSTUP app.py, ukládání i
├── main.py
├── schema.py
├── selenium_sol_depraced # stare reseni pomoci selenium, stahuje celej html, asi funkcni, ale neefektivni
│           └── sel.py
├── sitemap_articles_0.xml #VSTUP sem musite dat
├── templates
│           ├── index.html
│           └── results.html
├── results.db #VYSTUP app.py, vysledna databaze s tabulkami COMMENTS a USERS
├── word_list.py #vygeneruje query a vypise na strout vysledek
├── words.json #VYSTUP word_list.py
└── words.txt #VSTUP word_list.py, slova ktera maji byt hledana