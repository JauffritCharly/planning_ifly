document.addEventListener('DOMContentLoaded', function() {
  const jsonUrl = 'planning.json?cache_buster=' + new Date().getTime();
  const container = document.getElementById('planning');

  const today = new Date();
  today.setHours(0,0,0,0);

  fetch(jsonUrl)
    .then(res => res.json())
    .then(planning => {

      // 🔥 TRI DES DATES
      planning.sort((a, b) => new Date(a.date) - new Date(b.date));

      // 🔥 FILTRE : supprimer les jours passés
      const upcomingDays = planning.filter(day => {
        const date = new Date(day.date);
        date.setHours(0,0,0,0);
        return date >= today;
      });

      upcomingDays.forEach(day => {
        const column = document.createElement('div');
        column.className = 'day-column';

        const dateObj = new Date(day.date);
        dateObj.setHours(0,0,0,0);

        // 🔥 JOUR ACTUEL
        if (dateObj.getTime() === today.getTime()) {
          column.classList.add('today');
        }

        const options = { weekday: 'short', day: 'numeric', month: 'short' };
        const formattedDate = dateObj.toLocaleDateString('fr-FR', options);

        const title = document.createElement('div');
        title.className = 'day-title';
        title.innerText = formattedDate;

        column.appendChild(title);

        if (day.time_slots.length === 0) {
          const empty = document.createElement('div');
          empty.className = 'no-slot';
          empty.innerText = 'Aucun créneau';
          column.appendChild(empty);
        } else {
          day.time_slots.forEach(time => {

            const [hour, minute] = time.split(':').map(Number);

            const start = new Date(dateObj);
            start.setHours(hour, minute);

            const end = new Date(start);
            end.setMinutes(end.getMinutes() + 30);

            const timeString = `${hour.toString().padStart(2,'0')}:${minute.toString().padStart(2,'0')}`;
            const endString = end.toLocaleTimeString('fr-FR', {
              hour: '2-digit',
              minute: '2-digit'
            });

            const link = document.createElement('a');
            link.className = 'slot';
            link.href = 'https://www.iflyfrance.com/bons-cadeaux/utiliser-un-bon-ifly/';
            link.target = '_blank';
            link.innerText = `${timeString} - ${endString}`;

            column.appendChild(link);
          });
        }

        container.appendChild(column);
      });

    })
    .catch(err => console.error("Erreur :", err));
});