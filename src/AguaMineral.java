public class AguaMineral extends Bebidas {

    private String origen;

    public AguaMineral(String identificacion,String nombre, double litros, double precio, String marca) {
        super(identificacion, nombre, litros, precio, marca);
    }

    public AguaMineral(String identificacion, String nombre, double litros, double precio, String marca, String origen) {
        super(identificacion, nombre, litros, precio, marca);
        this.origen = origen;
    }

    public String getOrigen() {
        return origen;
    }

    public void setOrigen(String origen) {
        this.origen = origen;
    }
}


