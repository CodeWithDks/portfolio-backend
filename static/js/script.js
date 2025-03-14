let currentPage = 1;
const perPage = 10;

// Fetch submissions with pagination
function fetchSubmissions(page) {
    fetch(`/api/submissions?page=${page}&per_page=${perPage}`)
        .then(response => response.json())
        .then(data => {
            const submissionsDiv = document.getElementById('submissions');
            submissionsDiv.innerHTML = ''; // Clear previous submissions
            data.submissions.forEach(submission => {
                submissionsDiv.innerHTML += `
                    <div class="submission">
                        <p><strong>Name:</strong> ${submission.name}</p>
                        <p><strong>Email:</strong> ${submission.email}</p>
                        <p><strong>Message:</strong> ${submission.message}</p>
                        <hr>
                    </div>
                `;
            });

            // Update pagination controls
            document.getElementById('page-info').textContent = `Page ${data.page} of ${Math.ceil(data.total / data.per_page)}`;
            document.getElementById('prev-page').disabled = data.page === 1;
            document.getElementById('next-page').disabled = data.page === Math.ceil(data.total / data.per_page);
        })
        .catch(error => {
            console.error('Error fetching submissions:', error);
        });
}

// Search functionality
document.getElementById('search-button').addEventListener('click', () => {
    const query = document.getElementById('search-query').value;
    const field = document.getElementById('search-field').value;

    fetch(`/api/submissions/search?query=${query}&field=${field}`)
        .then(response => response.json())
        .then(data => {
            const submissionsDiv = document.getElementById('submissions');
            submissionsDiv.innerHTML = ''; // Clear previous submissions
            data.forEach(submission => {
                submissionsDiv.innerHTML += `
                    <div class="submission">
                        <p><strong>Name:</strong> ${submission.name}</p>
                        <p><strong>Email:</strong> ${submission.email}</p>
                        <p><strong>Message:</strong> ${submission.message}</p>
                        <hr>
                    </div>
                `;
            });
        })
        .catch(error => {
            console.error('Error searching submissions:', error);
        });
});

// Pagination event listeners
document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        fetchSubmissions(currentPage);
    }
});

document.getElementById('next-page').addEventListener('click', () => {
    currentPage++;
    fetchSubmissions(currentPage);
});

// Logout function
function logout() {
    fetch('/logout', { method: 'POST' })
        .then(() => window.location.href = '/login')
        .catch(error => console.error('Error logging out:', error));
}

// Initial fetch
fetchSubmissions(currentPage);