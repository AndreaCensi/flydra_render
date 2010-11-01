import os
from string import Template

script = """

dir = "images/";
    
function url_exists(url) {
    var http = new XMLHttpRequest();
    http.open('HEAD', url, false);
    http.send();
    return http.status != 404;
}

String.prototype.format = function(args) {
        var formatted = this;
        for (arg in args) {
            formatted = formatted.replace("{" + arg + "}", args[arg]);
        }
        return formatted;
};

function get_exp_id() {
   image  = $('#image').val()
    signal = $('#signal').val()
    group  = $('#group').val()
    signal_op  = $('#signal_op').val()
    interval  = $('#interval').val()
    
    exp_id = image+"-"+signal+"-"+signal_op+"-"+group+"-"+interval;
    return exp_id;
}

function get_data_id() {
    signal = $('#signal').val()
    group  = $('#group').val()
    interval  = $('#interval').val()
    
    data_id = signal + "-" + group + "-" + interval;
     
    return data_id;
}


function update_images(images2url) {
    for(image in images2url) {
        imgelement = "img#"+image;
        url = images2url[image];
        $(imgelement).attr("src", url);
        $(imgelement).parent().attr("href", url);
    }
}


function update_gui() {
    exp_id = get_exp_id();
    data_id = get_data_id();

    /* Example image url:
     images/contrast-vz-sign-noposts-between:image_mean.png
     */

    images2url = {
        'action': dir + "/" + exp_id + ":action.png",
        'var': dir + "/" + exp_id + ":image_var.png",
        'mean':  dir + "/" + exp_id + ":image_mean.png",
        'timecorr':  dir + "/" + exp_id + "_delayed:mean.png",
        'timecorrbest': dir + "/" + exp_id + "_delayed:best_delay.png",
        'autocorr': dir + "/" + data_id + ":cross_correlation.png"
    }
    
    /* Change urls */
    update_images(images2url);
    
    /* Change image names */
    
    image_name = $('#image :selected').text()    
    signal_name = $('#signal :selected').text()
    
    $('.image_name').text(image_name);
    $('.signal_name').text(signal_name);
    $('.exp_id').text(exp_id);
        
    message = (
'<span>See details for combination <a target="_blank" href="{exp_id}.html">{title}</a>. '+
' See details for action <a target="_blank" href="{data_id}.html">{data_title}</a>.' +
'</span>').format(
                           {'exp_id':exp_id, 'title': exp_id, 
                           'data_id': data_id, 'data_title': data_id});
        
        $('#status').html(message);
            

    try {
    if(!url_exists(action_url)) {
        $('#error').text('Combination not present; tell Andrea to generate ' 
        + exp_id );
    } else {
      /*  $('#error').text(''); */
    } 
    
    } catch(error) {
    /*   
    $('#error').text('Could not determine if configuration exists - does not work locally.');
      */  
    }
    
    
    $('#slider').slider("value", 0);
}

function slider_change(event, ui) {
    /*$('.delay').text(0);*/

    /*delay = $("#slider")*/
    delay = ui.value;
    
    exp_id = get_exp_id();

    delay_ms = Math.round( 1000 * delay * (1.0/60) );
    
    $('.delay').text( delay_ms + "ms"  );

    images2url = {
        timecorrdelay: dir + "/" + exp_id + "_delayed:delay" + delay + ".png"
    }
    update_images(images2url);
}


$(document).ready( function () {
    $("#slider").slider({min:-5,max:10,step:1,slide:slider_change, change:slider_change});
    $('select').change(update_gui);
    
    update_gui(); /* will call slide() value */
});
 

"""

css = """

body {
    font-family: Verdana, Tahoma;
}

div#allselectors {
    display: block;
    overflow: auto;
    margin: 0;
    margin-bottom: 1em;
    padding: 0.5em; 
    background-color: #ddf;
}

div.box {
    display: block;
    float: left;
    margin-right: 1em;
}    


div#display_area {
    clear: both;
}

div.retinal_box {
    float: left;
    width: 32%;
}

div.retinal_box P {
    padding: 1em;
    padding-top: 0.5em;
    padding-bottom: 0;
    font-style: italic;
    font-size: smaller;
}

img.retinal { width: 90%;  background-color: gray; }
div#timecorrdelay_box { clear: left; }

#status {
    clear: both; font-weight: bold; font-size: small;
}

#error { color: red; font-weight: bold; }

"""

header = Template("""
<html>
    <head>
        <title> Smooth analysis GUI </title>
        <style type="text/css">${css}</style>
        <script type="text/javascript" src="images/static/jquery/jquery.js"></script>   
        <script type="text/javascript">                                         
          ${script}                                        
        </script>      
        <script type="text/javascript" src="images/static/jquery/jquery.ui.js"></script>   
        
        <!-- Image zoom -->
        <script type="text/javascript" src="images/static/jquery/jquery.imageZoom.js"></script>
        <link rel="stylesheet" href="images/static/jquery/jquery.imageZoom.css"/>
        
        <link rel="stylesheet" href="images/static/jquery/ui-lightness/jquery-ui-1.8.5.custom.css"/>
        
        <script type="text/javascript"> 
            $$(document).ready( function () {
                $$('.zoomable').imageZoom();
            });       
        </script>

    </head>
<body>
    """).substitute(script=script, css=css)

main = """
<p>    
<span id="status">?</span>
<!--<span id="error">?</span>-->
</p>

<div id="display_area">

<div id="timecorrbest_box" class="retinal_box">
    <a class="zoomable" href="">
        <img id="timecorrbest" class="retinal" />
    </a>
    <p> Best correlation between 
        <span class="image_name">?</span>
        and
        <span class="signal_name">?</span>.
    </p>
</div>
<!--
<div id="action_box" class="retinal_box">
    <a class="zoomable" href="">
        <img id="action" class="retinal"/>
    </a>
    <p> Correlation between 
        <span class="image_name">?</span>
        and
        <span class="signal_name">?</span>.
    </p>
</div>-->

<div id="mean_box" class="retinal_box">
    <a class="zoomable" href="">
        <img id="mean" class="retinal"/>
    </a>
    <p> Expectation of <span class="image_name">?</span> </p>
    </p>
</div>

<div id="var_box" class="retinal_box">
    <a class="zoomable" href="">
        <img id="var" class="retinal" />
    </a>
    <p> Variance of <span class="image_name">?</span> </p>
</div>


<div id="timecorrdelay_box" class="retinal_box">
    <a class="zoomable" href="">
        <img id="timecorrdelay" class="retinal" />
    </a>
    <p> <div id="slider" style="background-color: red;"></div> </p>
    <p> Correlation between 
        <span class="image_name">?</span>
        and
        <span class="signal_name">?</span> (delayed by <span class="delay">?</span>).
    </p>
</div>


<div id="timecorr_box" class="retinal_box">
    <a class="zoomable" href="">
        <img id="timecorr" class="retinal" />
    </a>
    <p> Correlation in time between 
        <span class="image_name">?</span>
        and
        <span class="signal_name">?</span>.
    </p>
</div>

<div id="autocorr_box" class="retinal_box">
    <a class="zoomable" href="">
        <img id="autocorr" class="retinal" />
    </a>
    <p> Autocorrelation of
        <span class="signal_name">?</span>.
    </p>
</div>


</div>




"""

footer = """
</body>
</html>
"""


def write_select(f, name, choices, onchange=""):
    '''Writes the <select> element to f. choices is a tuple of (value, desc).''' 
    f.write('<select id="%s" name="%s">\n' % (name, name))
    for i, choice in enumerate(choices):
        value = choice[0]
        desc = choice[1]
        selected = 'selected="selected"' if i == 0 else ""
        f.write('\t<option value="%s" %s>%s</option>\n' % 
                (value, selected, desc))
              
    f.write('</select>\n\n')    

def write_select_box(f, desc, name, choices):
    f.write('<div class="box" id="box-%s">\n' % name)
    f.write('<span>%s</span>\n' % desc)
    write_select(f, name, choices)
    f.write('</div>\n\n')
    
def create_gui(dir):
    from mamarama_analysis.first_order import interval_specs, group_specs, \
    signal_specs, signal_op_specs, image_specs

    if not os.path.exists(dir):
        os.makedirs(dir)
    
    filename = os.path.join(dir, 'gui.html')
    print "Writing to %s" % filename
    f = open(filename, 'w')
    
    f.write(header)
    
    f.write('<div id="allselectors">\n')
    write_select_box(f, 'Retinal quantity', 'image', image_specs)                     
    write_select_box(f, 'Signal', 'signal', signal_specs)
    write_select_box(f, 'operation', 'signal_op', signal_op_specs)
    write_select_box(f, 'Sample group', 'group', group_specs)
    write_select_box(f, 'Interval', 'interval', interval_specs)
    f.write('<span style="clear:both"></span>')
    f.write('</div>')
    
    f.write(main)
    
    f.write(footer)
   

    filename = os.path.join(dir, 'gui2.html')
    print "Writing to %s" % filename
    f = open(filename, 'w')
    f.write("""
    <html>
    <head><title>Double GUI</title></head>
    <body>
    <iframe src="gui.html" width="100%" height="50%">
    </iframe>
    <iframe src="gui.html" width="100%" height="50%">
    </iframe>
    </body>
    </html>
    """)
    
    
    
    
    
    
    
