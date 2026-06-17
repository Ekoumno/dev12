import flet as ft
import json

def main(page: ft.Page):
    # Configuration stricte format Smartphone
    page.title = "Le Duel des Secrets"
    page.window_width = 380
    page.window_height = 650
    page.window_resizable = False
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK

    # Variables de session
    mon_pseudo = ""
    mon_code_salon = ""
    mon_secret = None
    nom_adversaire = "En attente..."
    secret_adversaire = None
    tentatives = 0

    # Éléments graphiques (Widgets)
    input_pseudo = ft.TextField(label="Ton Pseudo", width=250, text_align=ft.TextAlign.CENTER)
    input_salon = ft.TextField(label="Code du Salon", width=250, text_align=ft.TextAlign.CENTER)
    input_secret = ft.TextField(label="Nombre secret (1-1000)", keyboard_type=ft.KeyboardType.NUMBER, password=True, width=200, text_align=ft.TextAlign.CENTER)
    texte_attente = ft.Text("En attente de l'adversaire...", size=14, color="grey", italic=True)
    
    titre_jeu = ft.Text("🎯 Devine son nombre !", size=24, weight=ft.FontWeight.BOLD, color="blueaccent")
    info_salon_text = ft.Text("", size=12, color="grey")
    champ_saisie_jeu = ft.TextField(label="Ta proposition", keyboard_type=ft.KeyboardType.NUMBER, width=200, text_align=ft.TextAlign.CENTER)
    resultat_indice = ft.Text("", size=16, weight=ft.FontWeight.W_500)
    compteur_text = ft.Text("Tentatives : 0", size=12, color="grey")

    # --- ROUTAGE RÉSEAU SÉCURISÉ ---
    def sur_message_recu(e):
        nonlocal nom_adversaire, secret_adversaire
        try:
            # Flet envoie l'événement, le contenu est dans e.data
            data = json.loads(e.data)
            
            # On filtre pour s'assurer que c'est le même salon et pas notre propre message
            if data["salon"] != mon_code_salon or data["expediteur"] == mon_pseudo:
                return

            if data["type"] == "PARTAGE_SECRET":
                nom_adversaire = data["expediteur"]
                secret_adversaire = int(data["valeur"])
                
                # Si les deux secrets sont configurés, le duel s'ouvre
                if mon_secret is not None:
                    page.clean()
                    afficher_ecran_jeu()
                    page.update()
        except:
            pass

    def valider_connexion(e):
        nonlocal mon_pseudo, mon_code_salon
        if not input_pseudo.value or not input_salon.value:
            return
        mon_pseudo = input_pseudo.value
        mon_code_salon = input_salon.value
        
        # Abonnement officiel au serveur de communication global de Flet
        page.pubsub.subscribe(sur_message_recu)
        
        page.clean()
        afficher_ecran_choix_secret()
        page.update()

    def valider_secret(e):
        nonlocal mon_secret
        if not input_secret.value:
            return
        mon_secret = int(input_secret.value)
        
        # Enpaquetage des données de session
        message = {
            "salon": mon_code_salon,
            "type": "PARTAGE_SECRET",
            "expediteur": mon_pseudo,
            "valeur": mon_secret
        }
        # Diffusion sur la brique de communication globale
        page.pubsub.send_all(json.dumps(message))
        
        if secret_adversaire is None:
            btn_valider_secret.disabled = True
            input_secret.disabled = True
            page.add(texte_attente)
            page.update()
        else:
            page.clean()
            afficher_ecran_jeu()
            page.update()

    def verifier_proposition(e):
        nonlocal tentatives
        if not champ_saisie_jeu.value:
            return
        
        choix = int(champ_saisie_jeu.value)
        tentatives += 1
        compteur_text.value = f"Tentatives : {tentatives}"

        if choix < secret_adversaire:
            resultat_indice.value = "📈 C'est PLUS GRAND !"
            resultat_indice.color = "orange"
        elif choix > secret_adversaire:
            resultat_indice.value = "📉 C'est PLUS PETIT !"
            resultat_indice.color = "amber"
        else:
            resultat_indice.value = f"🎉 GAGNÉ en {tentatives} coups !"
            resultat_indice.color = "green"
            btn_deviner.disabled = True
            page.add(ft.ElevatedButton("Nouvelle Partie", on_click=recommencer_partie, bgcolor="green"))

        champ_saisie_jeu.value = ""
        page.update()

    def recommencer_partie(e):
        nonlocal mon_secret, secret_adversaire, tentatives
        mon_secret = None
        secret_adversaire = None
        tentatives = 0
        btn_deviner.disabled = False
        resultat_indice.value = ""
        input_secret.disabled = False
        btn_valider_secret.disabled = False
        champ_saisie_jeu.value = ""
        page.clean()
        afficher_ecran_choix_secret()
        page.update()

    btn_rejoindre = ft.ElevatedButton("Rejoindre le Duel", on_click=valider_connexion, bgcolor="blueaccent", color="white")
    btn_valider_secret = ft.ElevatedButton("Enregistrer mon secret", on_click=valider_secret, bgcolor="green", color="white")
    btn_deviner = ft.ElevatedButton("Valider", on_click=verifier_proposition, bgcolor="blueaccent", color="white")

    # --- CONSTRUCION DES ÉCRANS ---
    def afficher_ecran_connexion():
        page.add(
            ft.Container(height=40),
            ft.Text("⚔️ MULTIJOUEUR ⚔️", size=24, weight=ft.FontWeight.BOLD, color="blueaccent"),
            ft.Container(height=20),
            ft.Text("Utilisez le même Code de Salon à distance.", text_align=ft.TextAlign.CENTER, size=14, color="grey"),
            ft.Container(height=30),
            input_pseudo,
            input_salon,
            ft.Container(height=20),
            btn_rejoindre
        )

    def afficher_ecran_choix_secret():
        page.add(
            ft.Container(height=40),
            ft.Text("🔒 Ton Nombre Secret", size=24, weight=ft.FontWeight.BOLD, color="green"),
            ft.Container(height=20),
            ft.Text("Choisis le nombre que ton adversaire devra deviner.", text_align=ft.TextAlign.CENTER, size=14),
            ft.Container(height=40),
            input_secret,
            ft.Container(height=20),
            btn_valider_secret
        )

    def afficher_ecran_jeu():
        info_salon_text.value = f"Salon : {mon_code_salon} | Adversaire : {nom_adversaire}"
        page.add(
            ft.Container(height=20),
            titre_jeu,
            info_salon_text,
            ft.Container(height=40),
            champ_saisie_jeu,
            btn_deviner,
            ft.Container(height=40),
            resultat_indice,
            compteur_text
        )

    afficher_ecran_connexion()

# L'adresse 0.0.0.0 permet d'ouvrir le jeu au monde entier sur le port 8080
ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=10000)