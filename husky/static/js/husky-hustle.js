var labelType, useGradients, nativeTextSupport, animate;
var noAlert = true;
var isOpen  = false;
var timeOut = 12000;
var formID  = '';
var tID     = '';

$('.submit-form').bind('click', submitForm);
$('.post-to-social').bind('click', postToSocial);
$('.pre-set-amount').bind('change', setPreSetAmount);
$('.to-teacher').bind('change', setPreSetAmount);
$('.remove-items').bind('click', removeCartItems);
$('.select-all-items').bind('change', selectAllItems);
$('#modal-box-donation').on('show.bs.modal', function(e){ makeDonation(e.relatedTarget) });
$('#modal-box-reminder').on('show.bs.modal', function(e){ sendReminder(e.relatedTarget) });

/* Overlay Functions */
function clearMessage(out) {
    if (!out) out = timeOut;
    tID = setTimeout(function(){ $('.messages').empty(); }, out);
};

function showOverlay(overlay) {
    if (tID) clearTimeout(tID);
    if (!overlay) overlay = 'overlay';
    $('#'+overlay).css('display', 'block');
    $('#'+overlay).height($(document).height());
    $('#message').css('color','#000000');
    $('#message').css('margin-left','10px');
    $('#message').css('font-weight','bold');
    $('#message').html('Loading...Please Wait!');
};

function showOverlayTop(event) {
    $('.background-cover-top').css({
        display: 'block',
        width: '100%',
        height: $(document).height(),
        opacity: 0,
        'z-index': 1050
    }).animate({opacity: 0.5, backgroundColor: '#000'});
};

function hideOverlay(overlay, out) {
    if (!overlay) overlay = 'overlay';
    $('#'+overlay).css('display', 'none');
    clearMessage(out);
};

function showOverlayBox(overlay, layer) {
    //if box is not set to open then don't do anything
    if (isOpen === false) return;
    // set the properties of the overlay box, the left and top positions
    $(overlay).css({
        display: 'block',
        left: ($(window).width() - $(overlay).width())/2,
        top: 50,
        position: 'absolute'
    });
    // set the window background for the overlay. i.e the body becomes darker
    if (layer) {
        $('.background-cover-top').css({
            display: 'block',
            width: '100%',
            height: $(document).height()
        });
        $(overlay).css({ 'z-index': $(overlay).css('z-index')+layer });
    } else {
        $('.background-cover').css({
            display: 'block',
            width: '100%',
            height: $(document).height()
        });
    }
};

function doOverlayOpen(overlay, layer) {
    formID  = overlay;
    overlay = '#overlay-box-'+overlay;
    //set status to open
    isOpen = true;
    showOverlayBox(overlay, layer);
    if (layer) {
        $('.background-cover-top').css({opacity: 0}).animate({opacity: 0.5, backgroundColor: '#000'});
    } else {
        $('.background-cover').css({opacity: 0}).animate({opacity: 0.5, backgroundColor: '#000'});
    }
    // dont follow the link : so return false.
    return false;
};

function doOverlayClose(overlay, layer) {
    overlay = '#overlay-box-'+overlay;
    //set status to closed
    isOpen = false;
    $(overlay).css('display', 'none');
    // now animate the background to fade out to opacity 0
    // and then hide it after the animation is complete.
    if (layer) {
        $('.background-cover-top').animate( {opacity: 0}, 'fast', null, function() { $(this).hide(); } );
        $(overlay).css({ 'z-index': $(overlay).css('z-index')-layer });
    } else {
        $('.background-cover').animate( {opacity: 0}, 'fast', null, function() { $(this).hide(); } );
    }
};

function doOverlaySwap(close_overlay, open_overlay) {
    // close the current overlay
    overlay = '#overlay-box-'+close_overlay;
    //set status to closed
    isOpen = false;
    $(overlay).css('display', 'none');
    // open the next overlay
    overlay = '#overlay-box-'+open_overlay;
    //set status to open
    isOpen = true;
    showOverlayBox(overlay);
    return false;
};


/* Main Functions */
function reloadPage(event, id) {
    var url = window.location.href.replace( '#', '' );
    window.location = url;
};

function showFormDonate(event, id) {
    $('#overlay-box-add').dialog({
        closeOnEscape: true,
        minWidth: 600,
        minHeight: 100,
        modal: true,
        dialogClass: 'tooltip',
        resizable: false,
        close: function(event, ui) { cancelForm(); }
    });
};

function showFormTeacher(event, id) {
    $('#overlay-box-teacher').dialog({
        closeOnEscape: true,
        minWidth: 600,
        minHeight: 100,
        modal: true,
        dialogClass: 'tooltip',
        resizable: false,
        close: function(event, ui) { cancelForm(); }
    });
};

function showBarChart(type) {
    $.getJSON('/admin/reports/' + type, initBarChart);
};

function showTooltip(event) {
    var id = this.id.replace( '_tooltip', '' );
    $('#tooltip_'+id).dialog({
        closeOnEscape: true,
        minWidth: 500,
        minHeight: 100,
//		modal: true
        dialogClass: 'tooltip',
        resizable: false
    });
};

function submitForm(event) {
    var button = $(this);
    button.button('loading');
    var id = $(this).attr('id').match('submit_(\\w+)');
    var form = $('#'+ id[1] +'_form');
    var params = form.serialize();
    var action = form.attr('action');
// console.log( '####-params: ',params );
// console.log( '####-action: ',action );
    if (id[1] === 'invite') {
        if (!$('#email_addresses').val()) {
            alert('You must provide email addresses');
            return false;
        }
    }
    if (id[1] === 'reminder' || id[1] === 'thanks') {
        $('.set-reminder').each(
            function () {
                if ($(this).attr('checked') === 'checked') {
                    params += '&donators=' + $(this).val();
                }
            }
        );
    }
    $.ajax(
        {
            url: action,
            type: 'post',
            dataType: 'json',
            data: params,
            timeout: 35000,
            complete: function(results){ button.button('reset'); updateStatus(results.responseJSON) }
        }
    );
    return false;
};

function submitFormAction(event) {
    var id = this.id.replace( 'submit_', '' );
    var form = $('#'+ id +'_form');
    showOverlayTop();
    setTimeout(function(){ form.submit(); }, 1000);
};

function submitSearchForm(event) {
    var id  = this.id.replace( 'submit_', '' );
    var reg = new RegExp( '(\\w+)_(\\w+)' );
    var got = id.match( reg );
    if (got) {
        id = got[2];
        if (got[1] === 'parent') {
            $('#parent_only').val(1);
            $('#student_last_name').val('');
            $('#student_first_name').val('');
        } else {
            $('#parent_only').val(0);
            $('#parent_last_name').val('');
            $('#parent_first_name').val('');
        }
    }
    showOverlayTop();
    setTimeout(function(){ $('#form_'+ id).submit(); }, 1000);
};

function cancelOverlay(event) {
    var keyCode;
    if (event === null) {
        keyCode = event.keyCode;
    } else { // mozilla
        keyCode = event.which;
    }
    if (keyCode === 27) {
        if (formID.match('_form')) {
            $('#'+formID+' .cancel_button').trigger('click');
        } else if (formID === 'edit') {
            $('.form-'+formID+' .cancel_button').trigger('click');
        } else {
            $('#'+formID+'_form .cancel_button').trigger('click');
        }
        cancelForm(formID, formID);
        formID  = '';
    }
};

function cancelForm(event, cssClass) {
    var id  = $(this).attr('id');
    var form;
    if (id && typeof(id) != 'object') {
        doOverlayClose(id);
        if (id === 'cancel_child' || id === 'cancel_profile') {
            $('.form-edit').hide();
        } else if (id === 'cancel_sponsor') {
            var sponsor_id = $('#id').val();
            $('#sponsor').hide();
            $('#sponsor input').each(
                function () {
                    if (this.id) {
                        var text = $('#row'+sponsor_id+' td[abbr="'+this.id+'"]').text();
                        if (this.id === 'per_lap') {
                            $(this).attr('checked', false);
                        } else if (text) {
                            $(this).attr('value', '');
                        }
                    }
                }
            );
        } else {
            form = id.replace( 'cancel_', '' );
            $('#'+form+'_form').hide();
        }
    } else if (id && typeof(id) === 'object' && id.name === 'id') {
        $('.input-field').each(
            function () {
                $(this).attr('value', '');
            }
        );
    } else if (this.id && typeof(this.id) != 'object') {
        form = this.id.replace( 'cancel_', '' );
        $('#'+form+'_form').hide();
    }
};

function updatePage(data) {
    updateStatus(data);
    if (data['status'] != 200) return;
    cancelFormDetails(data['form']);
    path  = '/admin/index';
    path += '/limit/' + ($('#limit').val() ? $('#limit').val() : '10');
    path += '/offset/' + ($('#offset').val() ? $('#offset').val() : '0');
    setTimeout(function(){ top.location.href = path; }, 1200);
};

function updateStatus(data) {
    if (tID) clearTimeout(tID);
    var status_msg = $('.messages');
    if (data.status != 200) {
        status_msg.css('color','red');
    } else {
        status_msg.css('color','green');
    }
    if (data.is_modal) {
        $('#'+data.is_modal).modal('hide');
    }
    status_msg.append('<li>'+data.message+'</li>');
    clearMessage();
};

function updateReload(data) {
    updateStatus(data);
    setTimeout(function(){ top.location.href = path; }, 1200);
};

function setAllReminders(event) {
    var checked = $(this).attr('checked');
    $('.set-reminder').each(
        function () {
            $(this).attr('checked', checked ? true : false);
        }
    );
};

function setPreSetAmount(event) {
    var value = $(this).val();
    if (this.className.match('to-teacher')) {
            value = $('#id_teacher :selected').val();
            $('#id_first_name').attr('value', value);
    } else {
        if (value) {
            $('#id_donation').attr('value', value);
            $('#id_donation').attr('readonly', true);
        } else {
            $('#id_donation').attr('value', '');
            $('#id_donation').attr('readonly', false);
        }
    }
};

function makeDonation(object) {
    var id = object.id.match('payment-([\\w-]+)')[1];
    $('#donation_form').attr('action', object.getAttribute('action'));
    $('#donation_id').val(id);
    $('#donation_title').text('Make a Payment to ' + $('#student-'+object.id).text());
};

function sendReminder(object) {
    var id = object.id.match('reminder-([\\w-]+)')[1];
    $('#reminder_form').attr('action', object.getAttribute('action'));
    $('#reminder_title').text("Send a Reminder to " + $('#student-'+id).text() + "'s Sponsors ");
};

function disconnectSocial(event) {
    $.getJSON($(this).attr('src'), reloadPage);
    return false;
}

function runCalculations(event) {
    doOverlayOpen('none', 50);
    $.getJSON($(this).attr('href'), reloadPage);
    return false;
};

function postToSocial(event) {
    window.open($(this).attr('src'), '_social', 'height=200,width=550,resizable=yes,scrollbars=yes');
};

function selectAllItems(event) {
    var checked = $('.select-all-label').hasClass('active');
    $('.remove-item').each(
        function () {
            this.checked = checked ? false : true;
        }
    );
};

function removeCartItems(event) {
    var action = $('#cart_form').attr('action');
    var makeRequest = function (id) {
        var dfd = $.Deferred();
        $.ajax(
            {
                url: action + id,
                type: 'get',
                dataType: 'json',
                timeout: 3000,
                complete: function(){ dfd.resolve(); },
                error: function(){ makeRequest(id); }
            }
        );
        return dfd.promise();
    };
    var def = [];
    $('.remove-item').each(function() {
        if (this.checked) {
            def.push(makeRequest(this.id));
        }
    });
    $.when.apply($, def).done(reloadPage);
    return false;
};

(function() {
    var ua = navigator.userAgent,
        iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
        typeOfCanvas = typeof HTMLCanvasElement,
        nativeCanvasSupport = (typeOfCanvas === 'object' || typeOfCanvas === 'function'),
        textSupport = nativeCanvasSupport && (typeof document.createElement('canvas').getContext('2d').fillText === 'function');
    labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
    nativeTextSupport = labelType === 'Native';
    useGradients = nativeCanvasSupport;
    animate = !(iStuff || !nativeCanvasSupport);
})();

function initBarChart(json) {
    var barChart = new $jit.BarChart({
        injectInto: 'infovis',
        animate: true,
        orientation: 'vertical',
        barsOffset: 20,
        Margin: {
            top: 5,
            left: 5,
            right: 5,
            bottom: 5
        },
        labelOffset: 5,
        type: useGradients ? 'stacked:gradient' : 'stacked',
        showAggregates:true,
        showLabels:true,
        Label: {
            type: labelType,
            size: 13,
            family: 'Arial',
            color: 'white'
        },
        Tips: {
            enable: true,
            onShow: function(tip, elem, label) {
                tip.innerHTML = "<b>" + elem.name + "</b>: " + elem.value;
            }
        },
        Events: {
            enable: true,
            onClick: function(node, eventInfo, e) {
                url = '/admin/results/donations-by-teacher?id=' + node.label;
                if ( ! node.label ) {
                } else if (window.location.href.match('most-donations-by-child\\?id=0') && node.label) {
                    url = '/admin/results/most-donations-by-child?id=' + node.label;
                    window.parent.location = url;
                } else if (window.location.href.match('donations-by-teacher\\?id=0') && node.label) {
                    window.parent.location = url;
                } else if (window.location.href.match('donations-by-teacher\\?id=\\d+')) {
                    window.parent.location = '/admin/results/donations-by-teacher';
//                     window.parent.history.back();
                }
            }
        }
    });
    barChart.loadJSON(json);
};


function _console_log(data) {
    if (console && console.log) {
      console.log( "Sample of data:", data );
    }
}
