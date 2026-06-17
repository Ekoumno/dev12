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

    # Variables de session propres à CHAQUE joueur
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
    texte_attente = ft.Text("En attente que l'adversaire valide son secret...", size=14, color="grey", italic=True)
    
    titre_jeu = ft.Text("🎯 Devine son nombre !", size=24, weight=ft.FontWeight.BOLD, color="blueaccent")
    info_salon_text = ft.Text("", size=12, color="grey")
    champ_saisie_jeu = ft.TextField(label="Ta proposition", keyboard_type=ft.KeyboardType.NUMBER, width=200, text_align=ft.TextAlign.CENTER)
    resultat_indice = ft.Text("", size=16, weight=ft.FontWeight.W_500)
    compteur_text = ft.Text("Tentatives : 0", size=12, color="grey")
    btn_recommencer = ft.ElevatedButton("Nouvelle Partie", on_click=lambda e: recommencer_partie(), bgcolor="green", visible=False)

    # --- ROUTAGE RÉSEAU SIMULTANÉ (PubSub par Salon) ---
    def sur_message_recu(message_brut):
        nonlocal nom_adversaire, secret_adversaire
        try:
            # Sur Flet Web, les données du topic arrivent directement
            data = json.loads(message_brut)
            
            # Plus besoin de vérifier le salon manuellement car le topic gère l'isolation !

            # Cas 1 : L'adversaire partage son secret
            if data["type"] == "PARTAGE_SECRET":
                if data["expediteur"] != mon_pseudo:
                    nom_adversaire = data["expediteur"]
                    secret_adversaire = int(data["valeur"])
                    
                    # Si moi aussi j'ai déjà configuré mon secret, on lance le duel !
                    if mon_secret is not None:
                        page.clean()
                        afficher_ecran_jeu()
                        page.update()

            # Cas 2 : L'adversaire a gagné la partie
            elif data["type"] == "FIN_PARTIE":
                if data["gagnant"] != mon_pseudo:
                    resultat_indice.value = f"💥 Perdu ! {data['gagnant']} a trouvé en {data['coups']} coups !"
                    resultat_indice.color = "red"
                    btn_deviner.disabled = True
                    champ_saisie_jeu.disabled = True
                    btn_recommencer.visible = True
                    page.update()

            # Cas 3 : L'adversaire demande à rejouer
            elif data["type"] == "RESTART":
                if data["expediteur"] != mon_pseudo:
                    reinitialiser_variables_locales()
                    page.clean()
                    afficher_ecran_choix_secret()
                    page.update()

        except Exception as ex:
            print(f"Erreur décodage pubsub: {ex}")

    def valider_connexion(e):
        nonlocal mon_pseudo, mon_code_salon
        if not input_pseudo.value or not input_salon.value:
            return
        mon_pseudo = input_pseudo.value
        mon_code_salon = input_salon.value.strip() # Nettoie les espaces
        
        # S'abonner spécifiquement au CANAL (Topic) du numéro de salon
        page.pubsub.subscribe_topic(mon_code_salon, sur_message_recu)
        
        page.clean()
        afficher_ecran_choix_secret()
        page.update()

    def valider_secret(e):
        nonlocal mon_secret
        if not input_secret.value:
            return
        mon_secret = int(input_secret.value)
        
        # Construire le message
        message = {
            "type": "PARTAGE_SECRET",
            "expediteur": mon_pseudo,
            "valeur": mon_secret
        }
        # Envoyer uniquement sur les ondes du salon connecté
        page.pubsub.send_all_on_topic(mon_code_salon, json.dumps(message))
        
        # Si l'adversaire n'a pas encore envoyé le sien, on attend
        if secret_adversaire is None:
            btn_valider_secret.disabled = True
            input_secret.disabled = True
            page.add(texte_attente)
            page.update()
        else:
            # Si l'adversaire l'avait déjà envoyé, on bascule direct sur le plateau de jeu
            page.clean()
            afficher_ecran_jeu()
            page.update()

    def verifier_proposition(e):
        nonlocal tentatives
        if not champ_saisie_jeu.value or secret_adversaire is None:
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
            # On a trouvé le secret de l'adversaire !
            resultat_indice.value = f"🎉 GAGNÉ en {tentatives} coups !"
            resultat_indice.color = "green"
            btn_deviner.disabled = True
            champ_saisie_jeu.disabled = True
            btn_recommencer.visible = True
            
            # On informe immédiatement l'adversaire via le topic commun
            message_victoire = {
                "type": "FIN_PARTIE",
                "gagnant": mon_pseudo,
                "coups": tentatives
            }
            page.pubsub.send_all_on_topic(mon_code_salon, json.dumps(message_victoire))

        champ_saisie_jeu.value = ""
        page.update()

    def reinitialiser_variables_locales():
        nonlocal mon_secret, secret_adversaire, tentatives, nom_adversaire
        mon_secret = None
        secret_adversaire = None
        nom_adversaire = "En attente..."
        tentatives = 0
        btn_deviner.disabled = False
        champ_saisie_jeu.disabled = False
        input_secret.disabled = False
        input_secret.value = ""
        btn_valider_secret.disabled = False
        resultat_indice.value = ""
        compteur_text.value = "Tentatives : 0"
        btn_recommencer.visible = False

    def recommencer_partie():
        # Signaler sur le salon qu'on relance un match
        message_restart = {
            "type": "RESTART",
            "expediteur": mon_pseudo
        }
        page.pubsub.send_all_on_topic(mon_code_salon, json.dumps(message_restart))
        
        reinitialiser_variables_locales()
        page.clean()
        afficher_ecran_choix_secret()
        page.update()

    btn_rejoindre = ft.ElevatedButton("Rejoindre le Duel", on_click=valider_connexion, bgcolor="blueaccent", color="white")
    btn_valider_secret = ft.ElevatedButton("Enregistrer mon secret", on_click=valider_secret, bgcolor="green", color="white")
    btn_deviner = ft.ElevatedButton("Valider", on_click=verifier_proposition, bgcolor="blueaccent", color="white")

    # --- CONSTRUCTION DES ÉCRANS ---
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
            ft.Container(height=30),
            resultat_indice,
            compteur_text,
            ft.Container(height=20),
            btn_recommencer
        )

    afficher_ecran_connexion()

# Lancement officiel adapté à Render
ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=10000)