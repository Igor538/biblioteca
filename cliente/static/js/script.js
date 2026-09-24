const menuButton = document.getElementById("menuButton");
const navigation = document.getElementById("navigation");


/* ==============================
   MENU MOBILE
============================== */

if (menuButton && navigation) {

    menuButton.addEventListener("click", () => {

        navigation.classList.toggle("active");

    });

}


/* ==============================
   FECHAR MENU AO CLICAR
============================== */

const navigationLinks = document.querySelectorAll(
    ".navigation a"
);


navigationLinks.forEach((link) => {

    link.addEventListener("click", () => {

        navigation.classList.remove("active");

    });

});