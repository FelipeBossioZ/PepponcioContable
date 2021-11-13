import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;


public class Almacen {

    private Bebidas[][] estanteria;

    //CONSTRUCTOR

    public  Almacen(Bebidas[][] estanteria) {
        this.estanteria = estanteria;
    }

    public double precioTotal() {
        double total = 0;
        for (int i = 0; i < estanteria.length; i++) {
            for (int k = 0; k < estanteria[i].length; k++) {
                total = total + estanteria[i][k].getPrecio();

            }
        }
        System.out.println("Total todas las bebidas = $ " + total);
        return total;

    }

    public double totalPorMarca(String marca) {
        double totalMarca = 0;
        for (int i = 0; i < estanteria.length; i++) {
            for (int k = 0; k < estanteria[i].length; k++) {
                if (estanteria[i][k].getMarca() == marca) {
                    totalMarca = totalMarca + estanteria[i][k].getPrecio();
                }
            }
        }


        System.out.println("Precio Total por marca= $ " + totalMarca);
        return totalMarca;
    }

    public double precioEstanteria(int columna) {
        int precioPorEstanteria = 0;
        for (int i = 0; i <= estanteria[columna].length; i++) {

            precioPorEstanteria += +estanteria[i][columna].getPrecio();
        }

        System.out.println("Precio Por Estanteria (columna)= $" + precioPorEstanteria);
        return precioPorEstanteria;
    }


    public void eliminarProducto(String id) {
        Vacio vacio = new Vacio("null", "null", 0, 0, "null");

        for (int i = 0; i < estanteria.length; i++) {
            for (int j = 0; j < estanteria[i].length; j++) {
                if (estanteria[i][j].getIdentificacion() == id) {
                    estanteria[i][j] = vacio;
                }

            }

        }
    }

    public void agregarPodructo(Bebidas bebidaAgregada) {
        boolean productoExiste = false;

        for (int i = 0; i < estanteria.length; i++) {
            for (int j = 0; j < estanteria[i].length; j++) {
                if (estanteria[i][j].getIdentificacion().equals(bebidaAgregada.getIdentificacion())) {
                    productoExiste = true;
                }
            }
        }

        if (productoExiste == false) {
            for (int i = 0; i < estanteria.length; i++) {
                for (int j = 0; j < estanteria[i].length; j++) {
                    if (estanteria[i][j].getIdentificacion().equals("null")) {
                        estanteria[i][j] = bebidaAgregada;
                        break;
                    }
                }
                break;
            }
        }
    }


    public void mostrarInformacion() {
        String gaseosas = "";
        String aguas = "";

        for (int i = 0; i < estanteria.length; i++) {
            for (int j = 0; j < estanteria[i].length; j++) {
                if (estanteria[i][j].getIdentificacion().contains("A")) {
                    aguas += "ID: " + estanteria[i][j].getIdentificacion() + ", Nombre: " + estanteria[i][j].getNombre() + ", Marca: " + estanteria[i][j].getMarca() + ", Precio: $ " + estanteria[i][j].getPrecio() +
                            ", Litros: " + estanteria[i][j].getLitros() + ", Origen : " + ((AguaMineral) estanteria[i][j]).getOrigen() + "\r\n";
                }
                if (estanteria[i][j].getIdentificacion().contains("G")) {
                    gaseosas += "ID: " + estanteria[i][j].getIdentificacion() + ", Nombre: " + estanteria[i][j].getNombre() + ", Marca: " + estanteria[i][j].getMarca() + ", Precio: $ " + estanteria[i][j].getPrecio() +
                            ", Litros: " + estanteria[i][j].getLitros() + ", Azúcar(%) : " + ((BebidaSugar) estanteria[i][j]).getPorcentajeAzucar() + ", Promoción: " + (((BebidaSugar) estanteria[i][j]).isTienePromo() + "\r\n");
                }
            }
        }

        try {

            String ruta = "D:\\Programación\\Itellij IDEA\\TCS\\GaseosasYAguas.txt" ;
            String contenido = aguas + gaseosas;
            File file = new File(ruta);
            // Si el archivo no existe es creado
            if (!file.exists()) {
                file.createNewFile();
            }
            FileWriter fw = new FileWriter(file);
            BufferedWriter bw = new BufferedWriter(fw);
            bw.write(contenido);
            bw.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }



            // GETTER Y SETTER


            public Bebidas[][] getEstanteria () {
                return estanteria;
            }

            public void setEstanteria (Bebidas[][]estanteria){
                this.estanteria = estanteria;

            }
        }
