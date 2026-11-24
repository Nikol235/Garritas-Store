package pe.edu.upeu.garritas.common;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.List;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.server.ResponseStatusException;
class LocalImagesTest {
 @AfterEach void cleanup(){SecurityContextHolder.clearContext();}
 void role(String role){SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("user","",List.of(new SimpleGrantedAuthority(role))));}
 @Test void rejectsClientBeforeTouchingFilesOrDatabase(){
  role("ROLE_CLIENTE");var jdbc=mock(JdbcTemplate.class);var file=mock(org.springframework.web.multipart.MultipartFile.class);
  assertThrows(org.springframework.security.access.AccessDeniedException.class,()->new LocalImages(jdbc,"garritas-catalogo-ms").upload(1,file));
  verifyNoInteractions(jdbc,file);
 }
 @Test void rejectsSpoofedImageAndClosesSource() throws Exception {
  role("ROLE_ADMIN");var jdbc=mock(JdbcTemplate.class);boolean[] closed={false};
  var file=new MockMultipartFile("archivo","fake.png","image/png","<svg/>".getBytes()) {
   @Override public InputStream getInputStream() throws IOException {return new ByteArrayInputStream(getBytes()){@Override public void close() throws IOException {closed[0]=true;super.close();}};}
  };
  assertThrows(ResponseStatusException.class,()->new LocalImages(jdbc,"garritas-catalogo-ms").upload(1,file));
  assertTrue(closed[0]);verifyNoInteractions(jdbc);
 }
 @Test void rejectsHugeDimensionsEvenWhenCompressedFileIsSmall() throws Exception {
  role("ROLE_ADMIN");var jdbc=mock(JdbcTemplate.class);var out=new ByteArrayOutputStream();ImageIO.write(new BufferedImage(5000,2,BufferedImage.TYPE_INT_RGB),"png",out);
  assertTrue(out.size()<5000);
  var file=new MockMultipartFile("archivo","wide.png","image/png",out.toByteArray());
  var error=assertThrows(ResponseStatusException.class,()->new LocalImages(jdbc,"garritas-catalogo-ms").upload(1,file));
  assertEquals(400,error.getStatusCode().value());verifyNoInteractions(jdbc);
 }
}
