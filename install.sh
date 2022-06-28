mkdir -p ~/nbk/;
mkdir -p ~/nbk/data/;
cp dist/nbk ~/nbk/nbk;

installContent="\n#nbk\nexport PATH=\$PATH:~/nbk/";

if grep -Fxq "$installContent" ~/.bashrc
then
	echo "Already installed path to ~/.bashrc"
else
	echo -e "$installContent" >> ~/.bashrc
	echo "Succesfully added path to ~/.bashrc"
fi
