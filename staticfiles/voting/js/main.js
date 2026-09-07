// ── ChainVote Frontend JS ─────────────────────────────────

// 1. Enable submit button only when a candidate is selected
document.addEventListener('DOMContentLoaded', function () {

  const radios = document.querySelectorAll('.candidate-radio');
  const submitBtn = document.getElementById('submitBtn');

  if (radios.length && submitBtn) {
    radios.forEach(function (radio) {
      radio.addEventListener('change', function () {
        submitBtn.disabled = false;
        submitBtn.textContent = '🗳 Submit Vote';
      });
    });
  }

  // 2. Confirm before submitting vote
  const voteForm = document.getElementById('voteForm');
  if (voteForm) {
    voteForm.addEventListener('submit', function (e) {
      const selected = document.querySelector('.candidate-radio:checked');
      if (!selected) {
        e.preventDefault();
        alert('Please select a candidate before submitting.');
        return;
      }
      const candidateName = selected
        .closest('.candidate-card')
        .querySelector('.candidate-name').textContent;

      const confirmed = confirm('Confirm your vote for "' + candidateName + '"?\n\nThis action cannot be undone.');
      if (!confirmed) {
        e.preventDefault();
      }
    });
  }

  // 3. Auto-dismiss alert messages after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(function () { alert.remove(); }, 500);
    }, 5000);
  });

  // 4. Live results polling (if on results page with active election)
  const liveResults = document.getElementById('liveResults');
  if (liveResults && document.querySelector('.status-active')) {
    const electionId = window.location.pathname.match(/election\/(\d+)/);
    if (electionId) {
      setInterval(function () {
        fetch('/api/elections/' + electionId[1] + '/results/')
          .then(function (r) { return r.json(); })
          .then(function (data) {
            data.results.forEach(function (candidate) {
              const bar = document.querySelector('[data-candidate-id="' + candidate.candidate_id + '"] .result-bar');
              const stat = document.querySelector('[data-candidate-id="' + candidate.candidate_id + '"] .result-stat');
              if (bar) bar.style.width = candidate.vote_percentage + '%';
              if (stat) stat.textContent = candidate.vote_count + ' votes (' + candidate.vote_percentage + '%)';
            });
          })
          .catch(function () { /* silent fail */ });
      }, 10000); // poll every 10 seconds
    }
  }
});
