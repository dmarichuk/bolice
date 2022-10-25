from db import MongoConnection

def main():
    conn = MongoConnection()

    col = conn["asd"]

    r = col.find()
    print(r)

if __name__ == "__main__":
    main()    