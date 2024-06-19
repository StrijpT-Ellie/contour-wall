GITHUB_RELEASE=v0.1.0-beta
BASE_DOWNLOAD_URL=https://github.com/StrijpT-Ellie/contour-wall/releases/$GITHUB_RELEASE/

function init_rust {
	echo -e "\e[0;34mInitialising ContourWall environement for Rust in current directory\e[0;30m"

	# cargo init $project_name --bin
	output=$(cargo init $project_name --bin 2>&1)
	
	if [[ $? -ne 0 ]]; then
		echo -e "\n\e[1;31mFailed to initialise the Rust ContourWall development environement.\e[0m"
		echo -e "Failed command: \"cargo init "$project_name" --bin\" "
		echo -e "exiting..."
		exit 1
	fi
	
	output=$(cargo add contourwall 2>&1)
	
	if [[ $? -ne 0 ]]; then
		echo -e "\n\e[1;31mFailed to add package \"contourwall\" to your Cargo project\e[0m"
		echo -e "Link to cargo package: https://crates.io/crates/contourwall"
		echo -e "exiting..."
		exit 1
	fi
	
	echo -e "\e[1;32mSuccessfully initialised your ContourWall environement for Rust\e[0m"
	exit 0
}

function init_python {
	echo -e "\e[0;34mInitialising ContourWall environement for Python in current directory\e[0;30m"
	
	touch '$project_name'.py 
	exit 0
}

function init_bare {
	echo -e "\e[0;34mPulling the core library binary\e[0;30m"
	mkdir $project_name
	cd $project_name
	output=$(curl -f -o contourwall_core_linux.so $BASE_DOWNLOAD_URL$GITHUB_RELEASE/contourwall_core_linux.so 2>&1)
	if [[ $? -ne 0 ]]; then
		echo -e "\e[1;31mFailed to download binary from Github release ${GITHUB_RELEASE}\e[0m"
		echo -e "exiting..."
		exit 1
	fi
	echo -e "\e[1;32mSuccessfully initialised your Contour Wall environment\e[0m"
	exit 0
}

echo -e "\e[1;37mWelcome to ContourWall!\e[0m\n"
echo -e "This script uses Github release:" ${GITHUB_RELEASE}
echo -e "This script will setup the development enviroment for the ContourWall. If at anytime you want to quit this script, press: ctrl + c\n"

echo -e $BASE_DOWNLOAD_URL

read -p "What is the name of your project?
> " project_name

echo ""

read -p "What language do you want to use:
1) Python
2) Rust
3) Bare (no language, just binary)
4) Quit initialisation
> " choice

echo ""

if [[ $choice -eq 1 || $choice == "python" || $choice == "Python" ]]; then
	init_python
elif [[ $choice -eq 2 || $choice == "rust" || $choice == "Rust" ]]; then
	init_rust
elif [[ $choice -eq 3 || $choice == "bare" || $choice == "Bare" ]]; then
	init_bare
elif [[ $choice -eq 4 ]]; then
	exit 0
else

	echo -e "\n'"$choice"'" "is not a choice.\nexiting..."
	exit 1
fi