// ===== Confirmation générale =====
document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll("form");
    forms.forEach(form => {
        form.addEventListener("submit", function (e) {
            const btn = form.querySelector("button[type='submit']");
            if (btn && btn.textContent.toLowerCase().includes("supprimer")) {
                if (!confirm("Êtes-vous sûr de vouloir supprimer ?")) {
                    e.preventDefault();
                }
            }
        });
    });
});

// ===== Filtre par statut (optionnel) =====
function filtrerTests() {
    const filtre = document.getElementById("filtre-statut").value;
    const rows = document.querySelectorAll("#table-tests tbody tr");
    rows.forEach(row => {
        const statut = row.querySelector("td:nth-child(3)").textContent;
        if (filtre === "Tous" || statut === filtre) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

// Si on ajoute un select pour filtre
const selectFiltre = document.getElementById("filtre-statut");
if (selectFiltre) {
    selectFiltre.addEventListener("change", filtrerTests);
}
