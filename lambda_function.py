import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Inicializar recurso de DynamoDB y referencia a la tabla
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('EstudiantesEvento')


def lambda_handler(event, context):
    """
    Función principal que enruta las peticiones según el método HTTP
    y el path recibido desde API Gateway.
    """
    http_method = event.get('httpMethod')
    path_params = event.get('pathParameters') or {}
    student_id = path_params.get('id')

    try:
        if http_method == 'POST':
            return registrar_estudiante(event)

        elif http_method == 'GET' and student_id is None:
            return listar_estudiantes()

        elif http_method == 'GET' and student_id is not None:
            return consultar_estudiante(student_id)

        elif http_method == 'DELETE' and student_id is not None:
            return eliminar_estudiante(student_id)

        else:
            return build_response(400, {"mensaje": "Operación no soportada"})

    except Exception as e:
        return build_response(500, {"mensaje": f"Error interno: {str(e)}"})


def registrar_estudiante(event):
    """
    POST /estudiantes
    Registra un nuevo estudiante en DynamoDB.
    """
    body = json.loads(event.get('body', '{}'))

    # Validar campos obligatorios
    campos_requeridos = ['id', 'nombres', 'apellidos', 'correo', 'carrera', 'ciclo', 'fechaRegistro']
    for campo in campos_requeridos:
        if campo not in body:
            return build_response(400, {"mensaje": f"Falta el campo obligatorio: {campo}"})

    table.put_item(Item=body)

    return build_response(201, {
        "mensaje": "Estudiante registrado correctamente",
        "id": body['id']
    })


def listar_estudiantes():
    """
    GET /estudiantes
    Retorna la lista completa de estudiantes registrados.
    """
    response = table.scan()
    items = response.get('Items', [])

    return build_response(200, items)


def consultar_estudiante(student_id):
    """
    GET /estudiantes/{id}
    Busca un estudiante específico por su ID.
    """
    response = table.get_item(Key={'id': student_id})
    item = response.get('Item')

    if not item:
        return build_response(404, {"mensaje": "No se encontró el estudiante solicitado"})

    return build_response(200, item)


def eliminar_estudiante(student_id):
    """
    DELETE /estudiantes/{id}
    Elimina un estudiante por su ID.
    """
    # Verificar que el estudiante existe antes de eliminar
    response = table.get_item(Key={'id': student_id})
    if not response.get('Item'):
        return build_response(404, {"mensaje": "No se encontró el estudiante solicitado"})

    table.delete_item(Key={'id': student_id})

    return build_response(200, {"mensaje": "Estudiante eliminado correctamente", "id": student_id})


def build_response(status_code, body):
    """
    Construye una respuesta HTTP compatible con API Gateway,
    incluyendo headers CORS y serialización de tipos Decimal.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=decimal_default, ensure_ascii=False)
    }


def decimal_default(obj):
    """Convierte objetos Decimal (tipo numérico de DynamoDB) a int/float para JSON."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError
