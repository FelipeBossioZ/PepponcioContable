public abstract class Bebidas {

    //ATRIBUTOS
    private String identificacion;
    private String nombre;
    private double litros;
    private double precio;
    private String marca;

    //CONTRUCTOR

    public Bebidas(String identificacion, String nombre, double litros, double precio, String marca){
        this.identificacion = identificacion;
        this.nombre = nombre;
        this.litros = litros;
        this.precio = precio;
        this.marca = marca;
    }



    public String getIdentificacion() {
        return identificacion;
    }

    public void setIdentificacion(String identificacion) {
        this.identificacion = identificacion;
    }

    public double getLitros() {
        return litros;
    }

    public void setLitros(double litros) {
        this.litros = litros;
    }

    public double getPrecio() {
        return precio;
    }

    public void setPrecio(double precio) {
        this.precio = precio;
    }

    public String getMarca() {
        return marca;
    }

    public void setMarca(String marca) {
        this.marca = marca;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }
}
