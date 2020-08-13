find . -name "*.cpp" -o -name "*.c" -o -name "*.h" -o -name "*.hpp" > cscope.files
uncrustify -c /home/hy/Tools/tools/BeautifyCode/hy_c_c++.cfg --no-backup -F cscope.files
