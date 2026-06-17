# 1. Utilise une version de Python légère
FROM python:3.9

# 2. Définit le dossier de travail dans le conteneur
WORKDIR /code

# 3. Copie ton fichier requirements.txt et installe les bibliothèques
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 4. Copie tout le reste de ton code (app.py, etc.)
COPY . .

# 5. Indique le port sur lequel l'application doit écouter
EXPOSE 7860

# 6. La commande qui lance ton jeu
CMD ["python", "app.py"]