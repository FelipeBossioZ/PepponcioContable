

public class Main {

    public static void main(String[] args) {

        //CREAR ALMACEN

        //Bebidas Azucaradas
        BebidaSugar cocacola = new BebidaSugar("GC001", "CocaCola", 0.7, 1000, "CocaCola", 0.10, false);
        BebidaSugar sprite = new BebidaSugar("GC002", "Sprite", 0.7, 2000, "CocaCola", 0.5, true);
        BebidaSugar fanta = new BebidaSugar("GC003", "Fanta", 0.7, 3000, "CocaCola", 0.8, true);
        BebidaSugar cocaZero = new BebidaSugar("GC004", "CocaCola_Zero", 0.7, 4000, "CocaCola", 0.09, true);
        BebidaSugar manzana = new BebidaSugar("GP001", "Manzana", 0.7, 1000, "Postobon", 0.15, false);
        BebidaSugar colombiana = new BebidaSugar("GP002", "Colombiana", 0.7, 2000, "Postobon", 0.30, false);
        BebidaSugar naranjada = new BebidaSugar("GP003", "Naranjada", 0.7, 3000, "Postobon", 0.15, true);
        BebidaSugar uva = new BebidaSugar("GP004", "Uva", 0.7, 4000, "Postobon", 0.25, false);

        //AguaMineral
        AguaMineral manantial = new AguaMineral("AM001", "Manantial", 1, 2000, "AguaClara", "Manantial");
        AguaMineral cristal = new AguaMineral("AR002", "Cristal", 2500, 2000, "AguaClara", "Reserva");
        AguaMineral brisa = new AguaMineral("AR003", "Brisa", 1500, 2500, "Agua&Agua", "Reserva");
        AguaMineral oasis = new AguaMineral("AO004", "Oasis", 1200, 3000, "Oasis", "Oasis");

        // EspaciosVacios
        Vacio vacio = new Vacio("null", "null", 0, 0, "null");

        //Matriz
        Bebidas[][] estanteria = new Bebidas[4][3];
        estanteria[0][0] = cocacola;
        estanteria[0][1] = vacio;
        estanteria[0][2] = manantial;
        estanteria[1][0] = sprite;
        estanteria[1][1] = colombiana;
        estanteria[1][2] = vacio;
        estanteria[2][0] = fanta;
        estanteria[2][1] = vacio;
        estanteria[2][2] = brisa;
        estanteria[3][0] = vacio;
        estanteria[3][1] = uva;
        estanteria[3][2] = oasis;


        //METODOS ALMACEN
        Almacen almacen = new Almacen(estanteria);

        //Calcular precio de todas las bebidas:
        almacen.precioTotal();

        //Calcular el precio por marca:
        almacen.totalPorMarca("CocaCola");

        //Calcular el precio total de una estanteria:
        almacen.precioEstanteria(1);

        //Eliminar Producto:
        almacen.eliminarProducto("C001");

        //Agregar Producto:
        almacen.agregarPodructo(brisa);

        //Mostrar en .txt
        almacen.mostrarInformacion();
    }


}
