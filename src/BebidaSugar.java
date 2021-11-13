public class BebidaSugar extends Bebidas{


    private double porcentajeAzucar;
    private boolean tienePromo;


    //CONSTRUCTOR
    public BebidaSugar(String identificacion, String nombre, double litros, double precio, String marca) {
        super(identificacion, nombre, litros, precio, marca);
    }

    public BebidaSugar(String identificacion, String nombre, double litros, double precio, String marca, double porcentajeAzucar, boolean tienePromo) {
        super(identificacion, nombre, litros, precio, marca);
        this.porcentajeAzucar = porcentajeAzucar;
        this.tienePromo = tienePromo;
        descuento();
    }

    //METODOS
    public void descuento(){
        if (tienePromo){
            super.setPrecio(getPrecio() - (getPrecio() * 0.10));
        }
    }

    public double getPorcentajeAzucar() {
        return porcentajeAzucar;
    }

    public void setPorcentajeAzucar(double porcentajeAzucar) {
        this.porcentajeAzucar = porcentajeAzucar;
    }

    public boolean isTienePromo() {
        return tienePromo;
    }

    public void setTienePromo(boolean tienePromo) {
        this.tienePromo = tienePromo;
    }
}
