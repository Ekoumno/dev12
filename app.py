import flet as ft
import json
import os

def main(page: ft.Page):
    page.title = "Le Duel des Secrets"
    page.window_width = 380
    page.window_height = 650
    page.window_resizable = False
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK

    mon_pseudo = ""
    mon_code_salon = ""
    mon_secret = None
    nom_adversaire = "En attente..."
    secret_adversaire = None
    tentatives = 0

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

    def sur_message_recu(message_brut):
        nonlocal nom_adversaire, secret_adversaire
        try:
            data = json.loads(message_brut)
            if data["type"] == "PARTAGE_SECRET":
                if data["expediteur"] != mon_pseudo:
                    nom_adversaire = data["expediteur"]
                    secret_adversaire = int(data["valeur"])
                    if mon_secret is not None:
                        page.clean()
                        afficher_ecran_jeu()
                        page.update()
            elif data["type"] == "FIN_PARTIE":
                if data["gagnant"] != mon_pseudo:
                    resultat_indice.value = f"💥 Perdu ! {data['gagnant']} a gagné !"
                    resultat_indice.color = "red"
                    page.update()
        except Exception as ex:
            print(f"Erreur: {ex}")

    def valider_connexion(e):
        nonlocal mon_pseudo, mon_code_salon
        if not input_pseudo.value or not input_salon.value: return
        mon_pseudo = input_pseudo.value
        mon_code_salon = input_salon.value.strip()
        page.pubsub.subscribe_topic(mon_code_salon, sur_message_recu)
        page.clean()
        afficher_ecran_choix_secret()
        page.update()

    def valider_secret(e):
        nonlocal mon_secret
        if not input_secret.value: return
        mon_secret = int(input_secret.value)
        message = {"type": "PARTAGE_SECRET", "expediteur": mon_pseudo, "valeur": mon_secret}
        page.pubsub.send_all_on_topic(mon_code_salon, json.dumps(message))
        if secret_adversaire is None:
            btn_valider_secret.disabled = True
            page.add(texte_attente)
            page.update()
        else:
            page.clean()
            afficher_ecran_jeu()
            page.update()

    def verifier_proposition(e):
        nonlocal tentatives
        if not champ_saisie_jeu.value or secret_adversaire is None: return
        choix = int(champ_saisie_jeu.value)
        tentatives += 1
        if choix == secret_adversaire:
            resultat_indice.value = "🎉 GAGNÉ !"
            page.pubsub.send_all_on_topic(mon_code_salon, json.dumps({"type": "FIN_PARTIE", "gagnant": mon_pseudo}))
        page.update()

    def afficher_ecran_connexion():
        page.add(ft.Text("⚔️ MULTIJOUEUR ⚔️"), input_pseudo, input_salon, btn_rejoindre)

    def afficher_ecran_choix_secret():
        page.add(ft.Text("🔒 Ton Secret"), input_secret, btn_valider_secret)

    def afficher_ecran_jeu():
        page.add(titre_jeu, champ_saisie_jeu, btn_deviner, resultat_indice)

    btn_rejoindre = ft.ElevatedButton("Rejoindre", on_click=valider_connexion)
    btn_valider_secret = ft.ElevatedButton("Valider Secret", on_click=valider_secret)
    btn_deviner = ft.ElevatedButton("Deviner", on_click=verifier_proposition)

    afficher_ecran_connexion()

# Lancement propre pour Render
port = int(os.environ.get("PORT", 8080))
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")