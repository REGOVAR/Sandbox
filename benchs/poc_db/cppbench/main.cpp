#include "Variant.h"
#include <chrono>
#include <pqxx/pqxx> 

using namespace std;
using namespace chrono;
using namespace vcflib;
using namespace pqxx;


void normalize(long& pos, string& ref, string& alt)
{
    if (ref == alt)
    {
        // not a variant -> cancel it
        ref = ".";
        alt = ".";
    }

    while (ref.length() > 0 && alt.length() && ref.at(0) == alt.at(0))
    {
      ref = ref.substr(1);
      alt = alt.substr(1);
      ++pos;
    }

    if (ref.length() == alt.length())
    {
        while (ref.length() > 0 && alt.length() && ref.at(0) == alt.at(0))
        {
            ref = ref.substr(0, ref.length()-1);
            alt = alt.substr(0, alt.length()-1);
        }
    }
}



int main(int argc, char** argv)
{
    try
    {
        connection C("dbname=regovar-dev user=regovar password=regovar hostaddr=127.0.0.1 port=5433");
        if (C.is_open()) 
        {
           cout << "Opened database successfully: " << C.dbname() << endl;
        } 
        else 
        {
           cout << "Can't open database" << endl;
           return 1;
        }

        // check if tables exists
        string sql;
        sql = "SELECT EXISTS ( \
                 SELECT 1 \
                 FROM   information_schema.tables \
                 WHERE  table_name = '_9_variant' \
              );";

        nontransaction N(C);
        result R( N.exec( sql ));
        bool needToCreateTable = false;
        for (result::const_iterator c = R.begin(); c != R.end(); ++c) 
        {
          needToCreateTable = !c[0].as<bool>();
        }

        if (needToCreateTable)
        {
            cout << "Create table for poc cpp" << endl;
        }

        C.disconnect ();
    }
    catch (const exception &e)
    {
        cerr << e.what() << endl;
        return 1;
    }


    



    //return 0;


    time_point<system_clock> start, end;


    start = system_clock::now();
    VariantCallFile variantFile;

    if (argc > 1) 
    {
        string filename = argv[1];
        variantFile.open(filename);
    } 
    else 
    {
        variantFile.open(std::cin);
    }

    if (!variantFile.is_open()) 
    {
        return 1;
    }

    Variant var(variantFile);
    while (variantFile.getNextVariant(var)) 
    {
        //cout << "===== " << var.sequenceName << ", " << var.position << endl;

        /*
        for (auto& it : var.flatAlternates())
        {
            cout << "   >" << it.first   << " : ";
            for (auto& it2 : it.second) 
            {
                cout << "(" << var.sequenceName << ", " << it2.position << ", " << it2.ref << ", " << it2.alt << ") ";
            }
        }
        cout << endl;*/

        // first we normalize all alleles for this vcf entry
        vector<string> alts = var.alleles;
        vector<long> poss;
        vector<string> refs;
        for (uint i=0; i<alts.size(); i++)
        {
            poss.push_back(var.position);
            refs.push_back(var.ref);

            normalize(poss[i], refs[i], alts[i]);
        }

        // Then for each sample we register only "true" variant
        for (auto& it : var.samples) 
        {

            //cout << "  sample " << it.first << " (" << it.second["GT"][0] << ") : " ;
            vector<string> genotype;
            if (it.second["GT"][0].find('/') != std::string::npos)
            {
                genotype = split(it.second["GT"][0], '/');
            }
            else
            {
                genotype = split(it.second["GT"][0], '|');
            }


            if (genotype[0] != "."  && genotype[0] != "0")
            {
                int idx = stoi(genotype[0]);
                //cout << "[" << poss[idx] << ", " <<  refs[idx] << ", " << alts[idx] << "] ";
            }
            if (genotype[1] != "." && genotype[1] != "0")
            {
                int idx = stoi(genotype[1]);
                //cout << "[" << poss[idx] << ", " <<  refs[idx] << ", " << alts[idx] << "] ";
            }

            /*
            for (auto& it2 : it.second) 
            {


                cout << it2.first << "=" << it2.second[0] << " - ";
            }*/
            //cout << endl;
        }
        //cout << endl;
        
    }

    end = system_clock::now();
    duration<double> elapsed_seconds = end-start;
    cout << "parsing done in " << elapsed_seconds.count() << " s" << endl;

    return 0;

}