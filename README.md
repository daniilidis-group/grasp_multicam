# GRASP MultiCam

## How to build the website

	git checkout website

then edit the files in the "content" directory. When done:

	cd website
	
	hugo server -D

To test, point your browser to localhost:1313/grasp_multicam

If you are happy with the results, first commit the source code to
the "website" branch:

	git commit -a
	git push
	
If this is the first time you are doing it, clone the repo here
and check out the gh-pages branch:

    git clone https://github.com/daniilidis-group/grasp_multicam.git  public
	cd public
	git checkout gh-pages
    cd ..

Then run hugo once more to generate the files into the "public"
directory:

    hugo -D

Then commit/push the compiled web pages to the project page:

	cd public
	git commit -a
	git push




