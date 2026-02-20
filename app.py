from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secret"

db = SQLAlchemy(app)

# ================= CONTEXT PROCESSOR =================
@app.context_processor
def inject_now():
    return {
        'now': datetime.now,
        'datetime': datetime
    }

# ================= MODELES =================
class Projet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), nullable=False)
    client = db.Column(db.String(150))
    description = db.Column(db.Text)
    responsable = db.Column(db.String(150))
    semaine_prevue = db.Column(db.String(10))
    statut = db.Column(db.String(50), default="En cours")
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modules = db.relationship("Module", backref="projet", cascade="all, delete-orphan")

    def pourcentage_global(self):
        total_tests = sum(len(m.tests) for m in self.modules)
        total_valide = sum(len([t for t in m.tests if t.statut == "Validé"]) for m in self.modules)
        return int((total_valide / total_tests) * 100) if total_tests else 0

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    projet_id = db.Column(db.Integer, db.ForeignKey('projet.id'), nullable=False)
    tests = db.relationship('Test', backref='module', lazy=True, cascade="all, delete-orphan")

    def pourcentage_module(self):
        total = len(self.tests)
        if total == 0:
            return 0
        valide = len([t for t in self.tests if t.statut == "Validé"])
        return int((valide / total) * 100)

    def couleur_avancement(self):
        pct = self.pourcentage_module()
        if pct == 100:
            return "#28a745"
        elif pct >= 50:
            return "#ffc107"
        else:
            return "#dc3545"

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_test = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(50))
    priorite = db.Column(db.String(50))
    testeur = db.Column(db.String(100))
    systeme = db.Column(db.String(100))
    commentaire = db.Column(db.Text)
    anomalie = db.Column(db.Text)
    date_realisation = db.Column(db.Date)
    date_test_estimee = db.Column(db.String(10))
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    date_creation = db.Column(db.Date, default=date.today)
    date_modification = db.Column(db.Date, default=date.today, onupdate=date.today)

# ================= ROUTES PROJETS =================
@app.route("/")
def index():
    projets = Projet.query.all()
    return render_template("index.html", projets=projets)

@app.route("/ajouter_projet", methods=["GET","POST"])
def ajouter_projet():
    if request.method == "POST":
        projet = Projet(
            nom=request.form.get("nom"),
            client=request.form.get("client"),
            description=request.form.get("description"),
            responsable=request.form.get("responsable"),
            semaine_prevue=request.form.get("semaine_prevue"),
            statut=request.form.get("statut")
        )
        db.session.add(projet)
        db.session.commit()
        flash("Projet ajouté avec succès", "success")
        return redirect(url_for("index"))
    return render_template("ajouter_projet.html")

@app.route("/modifier_projet/<int:projet_id>", methods=["GET","POST"])
def modifier_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    if request.method == "POST":
        projet.nom = request.form.get("nom")
        projet.client = request.form.get("client")
        projet.description = request.form.get("description")
        projet.responsable = request.form.get("responsable")
        projet.semaine_prevue = request.form.get("semaine_prevue")
        projet.statut = request.form.get("statut")
        db.session.commit()
        flash("Projet modifié avec succès", "success")
        return redirect(url_for("index"))
    return render_template("modifier_projet.html", projet=projet)

@app.route("/supprimer_projet/<int:projet_id>", methods=["POST"])
def supprimer_projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    db.session.delete(projet)
    db.session.commit()
    flash("Projet supprimé !", "danger")
    return redirect(url_for("index"))

@app.route("/projet/<int:projet_id>")
def projet(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    testeur = request.args.get("testeur")
    statut = request.args.get("statut")
    priorite = request.args.get("priorite")
    critique = request.args.get("critique")
    for module in projet.modules:
        query = Test.query.filter_by(module_id=module.id)
        if testeur:
            query = query.filter(Test.testeur.contains(testeur))
        if statut and statut != "Tous":
            query = query.filter_by(statut=statut)
        if priorite and priorite != "Tous":
            query = query.filter_by(priorite=priorite)
        if critique and critique != "Tous":
            query = query.filter_by(critique=critique)
        module.tests = query.all()
    return render_template("projet.html", projet=projet)

@app.route("/projet/<int:projet_id>/tests")
def liste_tests(projet_id):
    projet = Projet.query.get_or_404(projet_id)

    tests = []
    for module in projet.modules:
        tests.extend(module.tests)

    return render_template("tests.html",
                           projet=projet,   
                           tests=tests)

# ================= ROUTES MODULES =================
@app.route("/ajouter_module/<int:projet_id>", methods=["GET","POST"])
def ajouter_module(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    if request.method == "POST":
        module = Module(nom=request.form.get("nom"), projet=projet)
        db.session.add(module)
        db.session.commit()
        flash("Module ajouté !", "success")
        return redirect(url_for("projet", projet_id=projet.id))
    return render_template("ajouter_module.html", projet=projet)

@app.route("/modifier_module/<int:module_id>", methods=["GET", "POST"])
def modifier_module(module_id):
    module = Module.query.get_or_404(module_id)
    if request.method == "POST":
        # Récupérer le nom du module depuis le formulaire
        module.nom = request.form.get("nom")
        db.session.commit()
        flash("Module modifié avec succès !", "success")
        return redirect(url_for("projet", projet_id=module.projet.id))
    return render_template("modifier_module.html", module=module)
    
@app.route("/supprimer_module/<int:module_id>", methods=["POST"])
def supprimer_module(module_id):
    module = Module.query.get_or_404(module_id)
    projet_id = module.projet.id
    db.session.delete(module)
    db.session.commit()
    flash("Module supprimé !", "danger")
    return redirect(url_for("projet", projet_id=projet_id))

# ================= ROUTES TESTS =================

from datetime import datetime

@app.route("/module/<int:module_id>/ajouter_test", methods=["GET","POST"])
@app.route("/module/<int:module_id>/ajouter_test", methods=["GET","POST"])
def ajouter_test(module_id):
    module = Module.query.get_or_404(module_id)
    if request.method == "POST":
        # Récupération des champs
        date_realisation_str = request.form.get("date_realisation")  # format yyyy-mm-dd
        date_test_estimee = request.form.get("date_test_estimee")  # format S1, S2, ...

        test = Test(
            nom_test=request.form.get("nom_test"),
            date_realisation=datetime.strptime(date_realisation_str, "%Y-%m-%d").date() if date_realisation_str else None,
            date_test_estimee=date_test_estimee,  # string: S1, S2...
            testeur=request.form.get("testeur"),
            systeme=request.form.get("systeme"),
            statut=request.form.get("statut"),
            priorite=request.form.get("priorite"),
            commentaire=request.form.get("commentaire"),
            module_id=module.id
        )

        db.session.add(test)
        db.session.commit()
        flash("Test ajouté avec succès !", "success")
        return redirect(url_for("projet", projet_id=module.projet.id))
    
    return render_template("ajouter_test.html", module=module)


@app.route("/modifier_test/<int:test_id>", methods=["GET","POST"])
def modifier_test(test_id):
    test = Test.query.get_or_404(test_id)
    if request.method == "POST":
    
        date_realisation_str = request.form.get("date_realisation")
        date_test_estimee = request.form.get("date_test_estimee")

        test.nom_test = request.form.get("nom_test")
        test.statut = request.form.get("statut")
        test.priorite = request.form.get("priorite")
        test.testeur = request.form.get("testeur")
        test.commentaire = request.form.get("commentaire")
        test.anomalie = request.form.get("anomalie")
        test.date_realisation = datetime.strptime(date_realisation_str, "%Y-%m-%d").date() if date_realisation_str else None
        test.date_test_estimee = date_test_estimee  # string S1, S2...
        test.impact_metier = request.form.get("impact_metier")

        db.session.commit()
        flash("Test modifié avec succès", "success")
        return redirect(url_for("projet", projet_id=test.module.projet.id))

    return render_template("modifier_test.html", test=test)

@app.route("/supprimer_test/<int:test_id>", methods=["POST"])
def supprimer_test(test_id):
    test = Test.query.get_or_404(test_id)
    projet_id = test.module.projet.id
    db.session.delete(test)
    db.session.commit()
    flash("Test supprimé !", "danger")
    return redirect(url_for("projet", projet_id=projet_id))

# ================= DASHBOARD =================
@app.route("/dashboard/<int:projet_id>")
def dashboard(projet_id):
    projet = Projet.query.get_or_404(projet_id)
    tests = [t for m in projet.modules for t in m.tests]
    total = len(tests)
    valides = sum(1 for t in tests if t.statut=="Validé")
    en_cours = sum(1 for t in tests if t.statut=="En cours")
    ko = sum(1 for t in tests if t.statut=="KO")
    non_testes = sum(1 for t in tests if t.statut=="Non testé")
    critiques_ko = sum(1 for t in tests if t.statut=="KO" and t.critique=="Oui")
    pourcentage_global = int((valides/total)*100) if total>0 else 0
    stats_modules = []
    for module in projet.modules:
        module_tests = module.tests
        m_total = len(module_tests)
        m_valide = sum(1 for t in module_tests if t.statut=="Validé")
        m_en_cours = sum(1 for t in module_tests if t.statut=="En cours")
        m_ko = sum(1 for t in module_tests if t.statut=="KO")
        m_pourcentage = int((m_valide/m_total)*100) if m_total>0 else 0
        stats_modules.append({
            "nom": module.nom,
            "total": m_total,
            "valide": m_valide,
            "en_cours": m_en_cours,
            "ko": m_ko,
            "pourcentage": m_pourcentage
        })
    testeurs = sorted({t.testeur for t in tests if t.testeur})
    return render_template("dashboard.html",
                           projet=projet,
                           total=total,
                           valides=valides,
                           en_cours=en_cours,
                           ko=ko,
                           non_testes=non_testes,
                           critiques_ko=critiques_ko,
                           pourcentage_global=pourcentage_global,
                           stats_modules=stats_modules,
                           testeurs=testeurs)


# CREATION DE LA BASE AUTOMATIQUE SI NECESSAIRE
with app.app_context():
    db.drop_all()    # supprime toutes les tables existantes
    db.create_all()  # crée toutes les tables selon les modèles actuels
    print("Base SQLite recréée avec toutes les colonnes actuelles !")

# RUN

if __name__ == "__main__":
    app.run(debug=True)
