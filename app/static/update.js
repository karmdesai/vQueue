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
                            Remove</a>
                        </span>
                        </div>`;

        return finalHTML;
    }

    setInterval(applyUpdate, 5000);
});