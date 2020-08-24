$(document).ready(function(){
    $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};

    function applyUpdate(){
        $.ajax({
        method: 'POST',
        url: {{ url_for('update')|tojson }},
        data: {'bName': '{{ bName }}'},
        success: function(response){
                $('.rCust').text(response.rCustomers);
        
                $('.myQ').empty();
        
                for (c = 0; c < response.rQueue.length; c++) {
                    var customerID = response.rQueue[c].cID;
                    var customerSize = response.rQueue[c].groupSize;
        
                    $('.myQ').append(returnHTML(customerID, customerSize));
                }
            }
        })
    }

    function returnHTML(customerID, customerSize){
        var finalHTML = `<div class="qCust"> 
                        <span class="cInfo">
                            Name: <strong>${customerID}</strong>, 
                            Size: <strong>${customerSize}</strong>
                        </span>
                        <span class="removeC">
                            <a href="${$SCRIPT_ROOT}/remove/${customerID}">
                            <svg width="1.2em" height="1.2em" viewBox="0 0 16 16" class="bi bi-x-circle-fill" fill="red" xmlns="http://www.w3.org/2000/svg">
                                <path fill-rule="evenodd" d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-4.146-3.146a.5.5 0 0 0-.708-.708L8 7.293 4.854 4.146a.5.5 0 1 0-.708.708L7.293 8l-3.147 3.146a.5.5 0 0 0 .708.708L8 8.707l3.146 3.147a.5.5 0 0 0 .708-.708L8.707 8l3.147-3.146z"/>
                            </svg>
                            Remove</a>
                        </span>
                        </div>`;

        return finalHTML;
    }

    setInterval(applyUpdate, 5000);
});