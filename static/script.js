document.getElementById("query-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const prompt = formData.get("prompt");

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt }),
        });

        const data = await response.json();
        const resultsDiv = document.getElementById("results");
        if (data.status === "success") {
            resultsDiv.innerHTML = `<h3>Query:</h3><pre>${data.query}</pre><h3>Results:</h3><pre>${JSON.stringify(data.results, null, 2)}</pre>`;
        } else {
            resultsDiv.innerHTML = `<h3>Error:</h3><pre>${data.message}</pre>`;
        }
    } catch (error) {
        console.error(error);
    }
});
