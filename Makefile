make:
	if test -f LTE-Sim; then rm LTE-Sim; fi;
	cat CONFIG/LTE-Sim
	sleep 2
	cd TOOLS; make; cd ../;
	./CONFIG/make_load-parameter-file.sh; 
	cd Debug; make clean; make; cd ..;
	ln -s Debug/LTE-Sim LTE-Sim 
	cat CONFIG/LTE-Sim-end
clean:
	rm LTE-Sim; cd Debug; make clean
	cd ..
	cd TOOLS; make clean;
	cd ..
	clear
	cat CONFIG/LTE-Sim-end-clear
	
