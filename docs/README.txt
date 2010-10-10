
These are instructions to create and upload the documentation.

Firstly, run:

     $ ./init_website.sh

This will download the gh-pages branch in website/.


Then, run:

     $ ./compile_website.sh

This compiles the .rst files in source/ into website/.

Finally, use:

     $ ./upload_website.sh

To commit and push to the gh-pages branch.

Note that when you add new pages to source/, you have to "git add" the resulting files in website/.