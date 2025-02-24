mkdir -p /usr/local/astrometry
mkdir -p /usr/local/astrometry/data

readonly ASTROMETRY_DATA_DIR="/usr/local/astrometry/data";

trap "exit" INT

for i in $( seq -w 7 19 ); do 
    wget http://data.astrometry.net/4100/index-41$i.fits; 
    mv index-41$i.fits $ASTROMETRY_DATA_DIR;
done

for i in $( seq -w 0 47 ); do 
    wget http://data.astrometry.net/4200/index-4202-$i.fits;
    mv index-4202-$i.fits $ASTROMETRY_DATA_DIR;
done

for i in $( seq -w 0 47 ); do 
    wget http://data.astrometry.net/4200/index-4203-$i.fits; 
    mv index-4203-$i.fits $ASTROMETRY_DATA_DIR;
done

for i in $( seq -w 0 47 ); do 
    wget http://data.astrometry.net/4200/index-4204-$i.fits;
    mv index-4204-$i.fits $ASTROMETRY_DATA_DIR;
done

for i in $( seq -w 0 11 ); do 
    wget http://data.astrometry.net/4200/index-4205-$i.fits;
    mv index-4205-$i.fits $ASTROMETRY_DATA_DIR; 
done

for i in $( seq -w 0 11 ); do 
    wget http://data.astrometry.net/4200/index-4206-$i.fits;
    mv index-4206-$i.fits $ASTROMETRY_DATA_DIR; 
done

for i in $( seq -w 0 11 ); do 
    wget http://data.astrometry.net/4200/index-4207-$i.fits; 
    mv index-4207-$i.fits $ASTROMETRY_DATA_DIR;
done

for i in $( seq -w 8 19 ); do 
    wget http://data.astrometry.net/4200/index-42$i.fits; 
    mv index-42$i.fits $ASTROMETRY_DATA_DIR;
done
