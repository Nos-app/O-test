document.addEventListener('DOMContentLoaded', () => {
    const cityInput = document.getElementById('cityInput');
    const suggestions = document.getElementById('suggestions');


    cityInput.addEventListener('input', async () => {
        const inputText = cityInput.value.trim();

        if (inputText.length >= 2) {
            try {
                const isLatin = /^[a-zA-Z\s]+$/.test(inputText);

                let apiUrl = 'https://geocoding-api.open-meteo.com/v1/search?';
                if (isLatin) {
                    apiUrl += 'language=en';
                } else {
                    apiUrl += 'language=ru';
                }

                const response = await fetch(`${apiUrl}&name=${inputText}&count=5&format=json`);
                const data = await response.json();
                console.log(data)
                suggestions.innerHTML = '';

                for (const city of data.results) {
                    const suggestionItem = document.createElement('div');
                    suggestionItem.textContent = city.name;
                    suggestionItem.classList.add('suggestion');
                    suggestions.classList.add('show');
                    suggestions.appendChild(suggestionItem);
                }
            } catch (error) {
                console.error('Ошибка при получении данных:', error);
            }
        } else {

            suggestions.innerHTML = '';
        }
    });


    suggestions.addEventListener('click', (event) => {
        if (event.target.classList.contains('suggestion')) {
            cityInput.value = event.target.textContent;
            suggestions.innerHTML = '';
        }
    });


    const cityButtons = document.querySelectorAll("#city");
    const form = document.querySelector("form");

    cityButtons.forEach(button => {
      button.addEventListener("click", function(event) {
        event.preventDefault();
        const cityName = button.value;
        cityInput.value = cityName;
        form.submit();
      });
    });
});
