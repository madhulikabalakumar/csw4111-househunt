<script>
    console.log("Script loaded");
    function toggleCheckboxes(category) {
        const checkboxes = document.querySelectorAll(`[data-category="${category}"]`);
        checkboxes.forEach(checkbox => {
            checkbox.parentElement.classList.toggle('d-none');
        });
    }

    function applyFilters() {
        const selectedFilters = {
            bldg_address: document.getElementById('bldg_address').value,
            bedrooms: document.getElementById('bedrooms').value,
            bathrooms: document.getElementById('bathrooms').value,
            furnishing_status: document.getElementById('furnishing_status').value,
            availability_status: document.getElementById('availability_status').value,
            max_price: document.getElementById('max_price').value,
            min_sq_footage: document.getElementById('min_sq_footage').value,
        };

        // Toggle visibility of checkboxes based on the selected filter category
        for (const category in selectedFilters) {
            toggleCheckboxes(category);
        }

        // Send an AJAX request to the server with selected filters
        fetch('/apply_filters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(selectedFilters),
        })
        .then(response => response.json())
        .then(data => {
            // Update the table with the filtered data
            // Implement this part based on your application's structure
            console.log(data);
        })
        .catch(error => {
            console.error('Error applying filters:', error);
        });
    }
</script>
