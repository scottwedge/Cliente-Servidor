#!/bin/bash
dir_ventilator=$1
echo $dir_ventilator
dir_sink=$2
file_name=$3
type_of_divide=$4
number_workers=$5
#number_workers = $(nproc)


#Corro el ventilator
gnome-terminal -- /bin/sh -c \
    '. /home/lenovo/anaconda3/bin/activate; python main.py \
    '$dir_ventilator' '$dir_sink' '$file_name' '$type_of_divide'' 

#Corro el sink 
gnome-terminal -- /bin/sh -c \
'. /home/lenovo/anaconda3/bin/activate; python sink.py '$dir_sink''
#Corro los workers
for ((c=1; c<=$number_workers; c++))
do
    gnome-terminal -- /bin/sh -c \
    '. /home/lenovo/anaconda3/bin/activate; python worker.py \
    '$dir_ventilator' '$dir_sink''
done
