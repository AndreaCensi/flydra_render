import os

script = """

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

function update_gui() {

    image  = $('#image').val()
    signal = $('#signal').val()
    group  = $('#group').val()
    signal_op  = $('#signal_op').val()
    interval  = $('#interval').val()
    
    exp_id = image+"-"+signal+"-"+signal_op+"-"+group+"-"+interval;
    
    data_id = signal + "-" + group + "-" + interval;
    
    dir = "images/";
    
    /* Example image url:
     images/contrast-vz-sign-noposts-between:image_mean.png
     */

    action_url = dir + "/" + exp_id + ":action.png";
    var_url = dir + "/" + exp_id + ":image_var.png";
    mean_url = dir + "/" + exp_id + ":image_mean.png";
    timecorr_url = dir + "/" + exp_id + "_delayed:mean.png";
    timecorrbest_url = dir + "/" + exp_id + "_delayed:best_delay.png";
    
    /* Change urls */
    
    $("img#action").attr("src", action_url);
    $("img#mean").attr("src", mean_url);
    $("img#var").attr("src", var_url);
    $("img#timecorr").attr("src", timecorr_url);
    $("img#timecorrbest").attr("src", timecorrbest_url);
     
    /* Change image names */
    
    image_name = $('#image :selected').text()    
    signal_name = $('#signal :selected').text()
    
    $('.image_name').text(image_name);
    $('.signal_name').text(signal_name);
    $('.exp_id').text(exp_id);
    
    if(url_exists(action_url)){
        $('#status').text('');
            message = (
'<span>See details for combination <a target="_blank" href="{exp_id}.html">{title}</a>. '+
' See details for action <a target="_blank" href="{data_id}.html">{data_title}</a>.' +
'</span>').format(
                           {'exp_id':exp_id, 'title': exp_id, 
                           'data_id': data_id, 'data_title': data_id});
        
        $('#status').html(message);
            
    } else {
        $('#status').text('Combination not present; tell Andrea to generate ' 
        + exp_id );
    }
    
}


$(document).ready(update_gui);

$(document).ready( function () {
    $('select').change(update_gui);
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

p#status {
    clear: both; font-weight: bold; font-size: small;
}

"""

header = """
<html>
    <head>
        <title> Smooth analysis GUI </title>
        <style type="text/css">{css}</style>
        <script type="text/javascript" src="images/static/jquery/jquery.js"></script>   
        <script type="text/javascript">                                         
          {script}                                        
        </script>      
    </head>
<body>
    """.format(script=script,css=css)

main = """
    
<div id="display_area">

<div id="action_box" class="retinal_box">
    <img id="action" class="retinal"/>
    <p> Correlation between 
        <span class="image_name">?</span>
        and
        <span class="signal_name">?</span>.
    </p>
</div>

<div id="mean_box" class="retinal_box">
    <img id="mean" class="retinal"/>
    <p> Expectation of <span class="image_name">?</span> </p>
    </p>
</div>

<div id="var_box" class="retinal_box">
    <img id="var" class="retinal" />
    <p> Variance of <span class="image_name">?</span> </p>
</div>

<div id="timecorr_box" class="retinal_box">
    <img id="timecorr" class="retinal" />
    <p> Autocorrelation of <span class="signal_name">?</span> </p>
</div>

<div id="timecorrbest_box" class="retinal_box">
    <img id="timecorrbest" class="retinal" />
    <p> Best correlation between 
        <span class="image_name">?</span>
        and
        <span class="signal_name">?</span>.
    </p>
</div>


</div>

<p id="status">
    ?
</p>

"""

footer = """
</body>
</html>
"""


def write_select(f,name, choices, onchange=""):
    '''Writes the <select> element to f. choices is a tuple of (value, desc).''' 
    f.write('<select id="%s" name="%s">\n' % (name, name))
    for i, choice in enumerate(choices):
        value = choice[0]
        desc = choice[1]
        selected = 'selected="selected"' if i==0 else ""
        f.write('\t<option value="%s" %s>%s</option>\n' %
                (value, selected, desc))
              
    f.write('</select>\n\n')    

def write_select_box(f, desc, name, choices):
    f.write('<div class="box" id="box-%s">\n' % name)
    f.write('<span>%s</span>\n' % desc)
    write_select(f, name, choices)
    f.write('</div>\n\n')
    
def create_gui(dir):
    from mamarama_analysis.first_order import interval_specs, group_specs,\
    signal_specs, signal_op_specs, image_specs

    if not os.path.exists(dir):
        os.makedirs(dir)
    
    filename = os.path.join(dir, 'gui.html')
    print "Writing to %s" % filename
    f = open(filename, 'w')
    
    f.write(header)
    
    f.write('<div id="allselectors">\n')
    write_select_box(f,'Retinal quantity', 'image', image_specs)                     
    write_select_box(f,'Signal','signal', signal_specs)
    write_select_box(f,'Signal operation', 'signal_op', signal_op_specs)
    write_select_box(f,'Sample group', 'group', group_specs)
    write_select_box(f,'Interval','interval', interval_specs)
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
    
    
    
    
    
    
    
