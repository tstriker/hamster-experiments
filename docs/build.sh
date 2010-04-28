# builds documentation and pushes update
rm -Rf _build/
make html
python sphinxtogithub.py _build/html/
git stash
git checkout gh-pages
cp -R _build/html/* ../
git add ../*.html ../*.js ../objects.inv ../static/* ../sources
git commit -m "automatic documentation sync"
git push
git checkout master
git stash pop
