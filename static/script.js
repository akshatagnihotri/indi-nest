document.addEventListener('DOMContentLoaded', () => {
    // Custom Reticle Cursor Animation
    const cursor = document.getElementById('tp-cursor');
    const cursorRing = document.querySelector('.tp-cursor-ring');

    document.addEventListener('mousemove', (e) => {
        const x = e.clientX;
        const y = e.clientY;
        
        cursor.style.left = `${x}px`;
        cursor.style.top = `${y}px`;
        cursor.style.opacity = '1';
        
        cursorRing.style.left = `${x}px`;
        cursorRing.style.top = `${y}px`;
        cursorRing.style.opacity = '1';
    });

    document.addEventListener('mouseleave', () => {
        cursor.style.opacity = '0';
        cursorRing.style.opacity = '0';
    });

    // 3D Parallax Card Tilt Effect
    const tiltCards = document.querySelectorAll('[data-tilt="true"]');
    tiltCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            // Calculate rotation values (max 8 degrees tilt)
            const rotX = -(y / (rect.height / 2)) * 6;
            const rotY = (x / (rect.width / 2)) * 6;
            
            card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale3d(1.02, 1.02, 1.02)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
        });
    });

    // API DOM Elements
    const form = document.getElementById('prediction-form');
    const citySelect = document.getElementById('city');
    const locationSelect = document.getElementById('location');
    const sizeInput = document.getElementById('size_sqft');
    const predictBtn = document.getElementById('predict-btn');
    const retryBtn = document.getElementById('retry-btn');

    // Result States
    const statePlaceholder = document.getElementById('results-placeholder');
    const stateLoading = document.getElementById('results-loading');
    const stateDisplay = document.getElementById('results-display');
    const stateError = document.getElementById('results-error');
    const errorText = document.getElementById('error-text');

    // Display Fields
    const predictedRentVal = document.getElementById('predicted-rent');
    const summaryLocation = document.getElementById('summary-location');
    const summaryCity = document.getElementById('summary-city');
    const summaryConfig = document.getElementById('summary-config');
    const summarySize = document.getElementById('summary-size');
    const summaryCoords = document.getElementById('summary-coords');
    const summaryStatus = document.getElementById('summary-status');

    // Set results state helper
    function setResultsState(state) {
        statePlaceholder.style.display = 'none';
        stateLoading.style.display = 'none';
        stateDisplay.style.display = 'none';
        stateError.style.display = 'none';

        if (state === 'placeholder') statePlaceholder.style.display = 'flex';
        else if (state === 'loading') stateLoading.style.display = 'flex';
        else if (state === 'display') stateDisplay.style.display = 'flex';
        else if (state === 'error') stateError.style.display = 'flex';
    }

    // Format currency to Indian standard (e.g. 25,000)
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            maximumFractionDigits: 0
        }).format(amount);
    }

    // Fetch and populate cities dropdown
    async function loadCities() {
        try {
            const response = await fetch('/api/cities');
            if (!response.ok) throw new Error('Failed to load cities');
            const data = await response.json();
            
            citySelect.innerHTML = '<option value="" disabled selected>Select City</option>';
            data.cities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading cities:', error);
            const fallbacks = ['Delhi', 'Mumbai', 'Pune'];
            citySelect.innerHTML = '<option value="" disabled selected>Select City</option>';
            fallbacks.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
        }
    }

    // Fetch locations based on selected city
    async function loadLocations(city) {
        locationSelect.disabled = true;
        locationSelect.innerHTML = '<option value="" disabled selected>Loading locations...</option>';
        
        try {
            const response = await fetch(`/api/locations?city=${encodeURIComponent(city)}`);
            if (!response.ok) throw new Error('Failed to load locations');
            const data = await response.json();
            
            locationSelect.innerHTML = '<option value="" disabled selected>Select Locality</option>';
            
            if (data.locations && data.locations.length > 0) {
                data.locations.forEach(loc => {
                    const option = document.createElement('option');
                    option.value = loc;
                    option.textContent = loc;
                    locationSelect.appendChild(option);
                });
                locationSelect.disabled = false;
            } else {
                locationSelect.innerHTML = '<option value="" disabled selected>No locations found</option>';
            }
        } catch (error) {
            console.error('Error loading locations:', error);
            locationSelect.innerHTML = '<option value="" disabled selected>Error loading options</option>';
        }
    }

    // Field validation helper
    function validateField(element, validatorFn) {
        const value = element.value;
        const parent = element.parentElement;
        const isValid = validatorFn(value);

        if (!isValid) {
            parent.classList.add('has-error');
        } else {
            parent.classList.remove('has-error');
        }
        return isValid;
    }

    // Validate size input
    function isSizeValid(val) {
        const num = parseFloat(val);
        return !isNaN(num) && num >= 100 && num <= 50000;
    }

    // Input listeners for validation and dropdowns
    citySelect.addEventListener('change', (e) => {
        validateField(citySelect, val => val !== "");
        loadLocations(e.target.value);
    });

    locationSelect.addEventListener('change', () => {
        validateField(locationSelect, val => val !== "");
    });

    sizeInput.addEventListener('input', () => {
        validateField(sizeInput, isSizeValid);
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Perform validation check
        const isCityOk = validateField(citySelect, val => val !== "");
        const isLocOk = validateField(locationSelect, val => val !== "");
        const isSizeOk = validateField(sizeInput, isSizeValid);

        if (!isCityOk || !isLocOk || !isSizeOk) {
            const firstError = document.querySelector('.has-error select, .has-error input');
            if (firstError) firstError.focus();
            return;
        }

        // Get Form Data
        const formData = new FormData(form);
        const payload = {
            city: formData.get('city'),
            location: formData.get('location'),
            property_type: formData.get('property_type'),
            size_sqft: parseFloat(formData.get('size_sqft')),
            bhk: parseFloat(formData.get('bhk')),
            numBathrooms: parseFloat(formData.get('numBathrooms')),
            numBalconies: parseFloat(formData.get('numBalconies')),
            Status: formData.get('Status')
        };

        // Transition results panel to loading
        setResultsState('loading');
        predictBtn.disabled = true;

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'An error occurred during prediction.');
            }

            const result = await response.json();
            
            // Format and display output parameters
            predictedRentVal.textContent = formatCurrency(result.predicted_price);
            
            summaryLocation.textContent = result.location;
            summaryCity.textContent = result.city;
            summaryConfig.textContent = `${payload.bhk} BHK · ${payload.numBathrooms} Bath · ${payload.numBalconies} Balcony`;
            summarySize.textContent = `${payload.size_sqft.toLocaleString()} Sq. Ft.`;
            summaryCoords.textContent = `${result.latitude.toFixed(4)}°, ${result.longitude.toFixed(4)}°`;
            summaryStatus.textContent = payload.Status;

            // Transition results panel to display
            setResultsState('display');
        } catch (error) {
            console.error('Prediction Error:', error);
            errorText.textContent = error.message || 'Unable to connect to the prediction backend.';
            setResultsState('error');
        } finally {
            predictBtn.disabled = false;
        }
    });

    // Fetch and render live data analysis metrics
    async function loadAnalysisData() {
        try {
            const response = await fetch('/api/analysis');
            if (!response.ok) throw new Error('Failed to load analysis metrics');
            const data = await response.json();
            
            // Populate KPI metrics
            document.getElementById('kpi-delhi').textContent = formatCurrency(data.avg_rent_by_city.Delhi);
            document.getElementById('kpi-mumbai').textContent = formatCurrency(data.avg_rent_by_city.Mumbai);
            document.getElementById('kpi-pune').textContent = formatCurrency(data.avg_rent_by_city.Pune);

            // Populate BHK Distribution Chart
            const bhkChart = document.getElementById('bhk-chart');
            bhkChart.innerHTML = '';
            const sortedBhk = Object.keys(data.bhk_dist).sort((a, b) => parseInt(a) - parseInt(b));
            sortedBhk.forEach(key => {
                const val = data.bhk_dist[key];
                const row = document.createElement('div');
                row.className = 'tp-chart-bar-row';
                row.innerHTML = `
                    <div class="tp-chart-bar-header">
                        <span class="tp-chart-bar-label">${key} BHK</span>
                        <span class="tp-chart-bar-val">${val}%</span>
                    </div>
                    <div class="tp-chart-bar-track">
                        <div class="tp-chart-bar-fill tp-chart-bar-fill-green" style="width: ${val}%"></div>
                    </div>
                `;
                bhkChart.appendChild(row);
            });

            // Populate Furnishing Impact Chart
            const furnishingChart = document.getElementById('furnishing-chart');
            furnishingChart.innerHTML = '';
            const statuses = Object.keys(data.avg_rent_by_status).sort();
            const maxPrice = Math.max(...Object.values(data.avg_rent_by_status));
            statuses.forEach(status => {
                const val = data.avg_rent_by_status[status];
                const pct = (val / maxPrice) * 100;
                const row = document.createElement('div');
                row.className = 'tp-chart-bar-row';
                row.innerHTML = `
                    <div class="tp-chart-bar-header">
                        <span class="tp-chart-bar-label">${status}</span>
                        <span class="tp-chart-bar-val">₹${formatCurrency(val)}</span>
                    </div>
                    <div class="tp-chart-bar-track">
                        <div class="tp-chart-bar-fill tp-chart-bar-fill-cyan" style="width: ${pct}%"></div>
                    </div>
                `;
                furnishingChart.appendChild(row);
            });

            // Handle Top Localities selection tabs
            const tabBtns = document.querySelectorAll('.tp-tab-btn');
            tabBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    tabBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    const selectedCity = btn.getAttribute('data-city');
                    renderLocalities(selectedCity, data.expensive_localities);
                });
            });

            // Render default localities list for Delhi
            renderLocalities('Delhi', data.expensive_localities);

        } catch (error) {
            console.error('Error loading analysis:', error);
        }
    }

    function renderLocalities(city, localitiesData) {
        const list = document.getElementById('localities-list');
        list.innerHTML = '';
        const cityLocs = localitiesData[city] || [];
        cityLocs.forEach((item, idx) => {
            const numStr = String(idx + 1).padStart(2, '0');
            const row = document.createElement('div');
            row.className = 'tp-locality-row';
            row.innerHTML = `
                <div class="tp-locality-name-group">
                    <span class="tp-locality-num">${numStr}</span>
                    <span class="tp-locality-name">${item.location}</span>
                </div>
                <div class="tp-locality-leader"></div>
                <span class="tp-locality-price">₹${formatCurrency(item.rent)} / mo</span>
            `;
            list.appendChild(row);
        });
    }

    // Reset and retry trigger
    retryBtn.addEventListener('click', () => {
        setResultsState('placeholder');
    });

    // Initialize application dropdowns
    loadCities();
    loadAnalysisData();
});
