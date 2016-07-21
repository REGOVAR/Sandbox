# C++ benchmark

## Get started

```sh

apt install ca-certificates git make g++ zlib1g-dev
git clone --recursive https://github.com/REGOVAR/REGOVAR.git
cd REGOVAR/benchs/poc_db/cppbench

wget http://pqxx.org/download/software/libpqxx/libpqxx-4.0.tar.gz
tar xvfz libpqxx-4.0.tar.gz
cd libpqxx-4.0
./configure
make
sudo make install

cd ..
make -j 25
./import_regovar
```

