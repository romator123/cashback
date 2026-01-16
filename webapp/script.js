let tg = window.Telegram.WebApp;

tg.expand(); // Раскрыть на весь экран

tg.MainButton.textColor = '#FFFFFF';
tg.MainButton.color = '#2cab37';

function sendData() {
    let bank = document.getElementById("bank").value;
    let category = document.getElementById("category").value;
    let percent = document.getElementById("percent").value;

    if (!category || !percent) {
        tg.showAlert("Пожалуйста, заполните все поля!");
        return;
    }

    let data = {
        bank: bank,
        category: category,
        percent: percent
    };

    // Отправляем данные боту в формате JSON строки
    tg.sendData(JSON.stringify(data));
}
