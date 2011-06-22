# copied from saccade_analysis.xxx.masteR_plot_gui

from StringIO import StringIO
from string import Template

css = """

body {
    margin: 0; padding: 0;
    font-family: Verdana, Tahoma;
    overflow-x: hidden;
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

#status {
    clear: both; font-weight: bold; font-size: small;
}

#error { color: red; font-weight: bold; }


#topbar {margin:0;  height: 9%; padding: 1em; display: block; }
#window {padding: 2px; margin:0;  width: 100%; height: 90%; border: 0;}

select { font-size: 120%; }


"""

scriptb = """


String.prototype.format = function(args) {
        var formatted = this;
        for (arg in args) {
            formatted = formatted.replace("{" + arg + "}", args[arg]);
        }
        return formatted;
};


function update_gui() {
    var data_id = get_data_id();

    var src = data_id + '.html';
    
    $('#window').attr("src", src); 

    message = (
    '<span><a target="_blank" '+
    'href="{data_id}.html">Open this page ({title}) in a new tab.</a>') .format(
                           { 'title': data_id, 
                           'data_id': data_id});
        
    $('#status').html(message);
}


$(document).ready( function () {
    $('select').change(update_gui);
    
    update_gui(); /* will call slide() value */
});
 
"""
page = """
<html>
    <head>
        <title> Saccade analysis GUI </title>
        <style type="text/css">${css}</style>
        <script type="text/javascript" src="images/static/jquery/jquery.js"></script>   
        <script type="text/javascript">                                         
          ${script}                                        
        </script>      
        <script type="text/javascript">                                         
          ${scriptb}                                        
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
<div id="container>
<div id="topbar">
    ${topbar}
    <p id="status">?</p>
</div>
<iframe  name="window"  src="#" id="window">
No iframes supported.
</iframe>
</div>
</body>
</html>
"""


def create_gui(filename, menus): 

    f = open(filename, 'w')
   
    script = StringIO()
    
    topbar = StringIO()

    script.write("""
function get_data_id() {
        var s = "";
    """)    
    for i, menu in enumerate(menus):
        label, choices, descriptions = menu
        name = 'var%d' % i
        
        key_desc = []
        for j in range(len(choices)):
            key_desc.append((choices[j], descriptions[j]))
    
        write_select_box(topbar, label, name, key_desc)
        
        if i != 0:
            script.write("""
        s = s + ".";
            """)
        script.write("""
        var%d = $('#var%d').val();
        s = s + var%d;
        """ % (i, i, i))
        
    script.write("""
    return s;
}
    """)     
    
    f.write(Template(page).substitute(css=css, script=script.getvalue(),
                                      scriptb=scriptb,
                                        topbar=topbar.getvalue()))
    
    

def create_gui_new(filename, menus): 
    f = open(filename, 'w')
   
    script = StringIO()
    
    topbar = StringIO()

    script.write("""
function get_data_id() {
        var s = "";
    """)    
    for i, menu in enumerate(menus):
        
        name, label, choices = menu
         
        write_select_box(topbar, label, name, choices)
        
        if i != 0:
            script.write("""
        s = s + ".";
            """)
        script.write("""
        %s = $('#%s').val();
        s = s + %s;
        """ % (name, name, name))
        
    script.write("""
    return s;
}
    """)     
    
    f.write(Template(page).substitute(css=css, script=script.getvalue(),
                                      scriptb=scriptb,
                                        topbar=topbar.getvalue()))
    

def write_select(f, name, choices):
    '''Writes the <select> element to f. choices is a tuple of (value, desc).''' 
    f.write('<select id="%s" name="%s">\n' % (name, name))
    for i, choice in enumerate(choices):
        value = choice[0]
        desc = choice[1]
        selected = 'selected="selected"' if i == 0 else ""
        f.write('\t<option value="%s" %s>%s</option>\n' % 
                (value, selected, desc))
              
    f.write('</select>\nwn')    

def write_select_box(f, desc, name, choices):
    f.write('<div class="box" id="box-%s">\n' % name)
    f.write('<span>%s</span>\n' % desc)
    write_select(f, name, choices)
    f.write('</div>\n\n') 
    
def create_main_gui(tabs, filename): 
    topbar = StringIO()
    
    topbar.write("""
<div id="tabs" class="widget">
    <ul class="tabnav">
""")
    
    for url, title, desc in tabs:
        topbar.write('    <li><a href="#%s">%s</a></li>\n' % (url, title))
        
    topbar.write("""
    </ul>
    
    """)
    
    for url, title, desc in tabs:
        topbar.write(' <div id="%s" class="container tabdiv">\n' % url)
        topbar.write('  <p class="desc"> %s </p>\n' % desc)
        topbar.write("""
        <iframe src="%s.html" class="window"> 
            No iframes supported. 
        </iframe>
""" % url)
    
        topbar.write('  </div>\n')
    topbar.write("""
</div> 
""")
    
    with open(filename, 'w') as f:
        f.write(Template("""
<html>
    <head>
        <title> Saccade analysis GUI </title>
        <style type="text/css"> 
        
body {
    padding: 0px;
    margin:0;
    font-family: Verdana, Tahoma;
    padding-left: 5px;
    padding-right: 5px;
    overflow-x: hidden;
    overflow-y: hidden;
}

.container {
display: block;
margin:0;padding:0;
width: 100%;
}

.window { 
    border: 0;
    height: 90%;
    width: 100%;
}


    .widget {
    width: 100%;
    margin: 0px;
    // padding: 10px;
    background: #f3f1eb;
    border: 1px solid #dedbd1;
    // margin-bottom: 15px;
    }

    .widget a {
    color: #222;
    text-decoration: none;
    }

    .widget a:hover {
    color: #009;
    text-decoration: underline;
    }

    .tabnav {
        margin: 0;
    }
    .tabnav li {
    display: inline;
    list-style: none;
    margin-left: 3em;        
        padding-left: 2em;
        padding-right: 2em;
        padding-top: 4px;
        padding-bottom: 4px;
    margin-bottom: 0;
    }

    .tabnav li a {
    text-decoration: none; 
    color: #222;
    font-weight: bold; 
    outline: none;
    margin-bottom: 0;
    }

    .tabnav li a:hover, .tabnav li a:active, .tabnav li.ui-tabs-selected a {
    background: #dedbd1;
    color: #222;
    text-decoration: none;
    }

    .tabdiv {
    margin-top: 0px;
    background: #fff;
    border-top: 10px solid #dedbd1; 
    padding-left: 5px;
    }

    

/* The only one important. */
.ui-tabs-hide {  
display: none;  
}  
.ui-tabs-selected {
background: #dedbd1;
}
        </style>
        <script type="text/javascript" src="images/static/jquery/jquery.js"></script>   
        <script type="text/javascript" src="images/static/jquery/jquery.ui.js"></script>   
        <script type="text/javascript">                                         
    
        $$(document).ready( function () {
            $$( "#tabs" ).tabs(); 
        });              
            
        </script>      
        
</head>
<body>
${topbar}
</body>
</html>
""").substitute(topbar=topbar.getvalue()))
    
    
    
    
